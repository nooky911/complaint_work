#!/usr/bin/env python3
"""Сохраняет согласованную копию рабочей БД и всего storage"""
import argparse
import datetime as dt
import fcntl
import gzip
import hashlib
import json
import os
import re
import shutil
import signal
import stat
import subprocess
import sys
import tarfile
import tempfile
import time
import uuid
from pathlib import Path, PurePosixPath
from zoneinfo import ZoneInfo

FORMAT = 'complaint_app_backup_v1'
CONFIG = Path('/etc/complaint-app-backup.json')
PROGRAM = Path('/usr/local/sbin/complaint-app-backup')
UNITS = Path('/etc/systemd/system')
CALENDAR = 'Fri *-*-* 03:00:00 Asia/Yekaterinburg'
DEFAULTS = {'format': FORMAT, 'project': '/data/complaint_app', 'database': 'complaint_work',
            'primary': '/var/backups/complaint_app', 'mirror': '/data/complaint_app/backups', 'days': 30}
NAME = re.compile(r'complaint-backup-\d{8}-\d{6}-[0-9a-f]{12}\.tar\Z')


def require(condition, message):
    """Останавливает операцию при нарушении обязательного условия"""
    if not condition:
        raise RuntimeError(message)


def log(message):
    """Выводит этап без паролей и содержимого базы"""
    print(message, flush=True)


def command(args, **kwargs):
    """Запускает команду без подстановок оболочки на хосте"""
    result = subprocess.run(args, stderr=subprocess.PIPE, **kwargs)
    require(result.returncode == 0, 'Не выполнена команда: ' + args[0] + '; ' + result.stderr.decode(errors='replace')[-1500:])
    return result


def checksum(path):
    """Вычисляет SHA-256 потоковым чтением"""
    with path.open('rb') as stream:
        return stream_hash(stream)


def stream_hash(stream):
    """Вычисляет контрольную сумму потока"""
    result = hashlib.sha256()
    for block in iter(lambda: stream.read(1024 * 1024), b''):
        result.update(block)
    return result.hexdigest()


def sync_dir(path):
    """Фиксирует изменения имён файлов на диске"""
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def atomic(path, content, mode=0o600):
    """Атомарно сохраняет небольшой служебный файл"""
    original = path.stat() if path.exists() else None
    fd, name = tempfile.mkstemp(prefix='.backup-write-', dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, mode)
        if original is not None and os.geteuid() == 0:
            os.chown(temporary, original.st_uid, original.st_gid)
        os.replace(temporary, path)
        sync_dir(path.parent)
    finally:
        temporary.unlink(missing_ok=True)


def save_json(path, value):
    """Сохраняет состояние операции в закрытый JSON-файл"""
    atomic(path, json.dumps(value, ensure_ascii=False, indent=2).encode())


def inventory(root):
    """Учитывает все имена storage без перехода по символическим ссылкам"""
    rows, unique, size = {}, set(), 0
    def visit(path):
        nonlocal size
        info = path.lstat()
        require(stat.S_ISREG(info.st_mode) or stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode),
                'В storage найден специальный файл: ' + str(path))
        rows[path.relative_to(root).as_posix()] = [info.st_mode, info.st_ino, info.st_dev,
            info.st_size, info.st_mtime_ns, info.st_ctime_ns, info.st_uid, info.st_gid, os.readlink(path) if path.is_symlink() else None]
        if stat.S_ISREG(info.st_mode) and (info.st_dev, info.st_ino) not in unique:
            unique.add((info.st_dev, info.st_ino)); size += info.st_size
        if stat.S_ISDIR(info.st_mode):
            for child in sorted(path.iterdir()):
                visit(child)
    visit(root)
    return rows, size + len(rows) * 2048


class Backup:
    """Управляет остановкой записи, проверкой двух копий и сроком хранения"""

    def __init__(self, config):
        self.config = config
        require(config.get('format') == FORMAT, 'Неизвестный файл настроек')
        self.project = Path(config['project']).resolve()
        self.storage = (self.project / 'storage').resolve()
        self.primary, self.mirror = Path(config['primary']).resolve(), Path(config['mirror']).resolve()
        require(self.project.is_dir() and self.storage.is_dir(), 'Не найдены проект или storage')
        require(re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', config['database']) and config['database'] not in ('postgres', 'template0', 'template1'), 'Недопустимое имя рабочей БД')
        require(config['days'] == 30, 'В этом задании согласовано хранение 30 суток')
        for target in (self.primary, self.mirror):
            require(target != Path('/') and not target.is_relative_to(self.storage) and not self.storage.is_relative_to(target), 'Копии и storage не должны содержать друг друга')
        require(self.mirror.is_relative_to(self.project) and not self.primary.is_relative_to(self.project), 'Дубль должен быть внутри проекта, основная копия — снаружи')
        require(not self.primary.is_relative_to(self.mirror) and not self.mirror.is_relative_to(self.primary), 'Нужны отдельные каталоги копий')
        compose = [self.project / name for name in ('docker-compose.yaml', 'docker-compose.yml') if (self.project / name).is_file()]
        require(len(compose) == 1, 'Нужен один существующий Compose-файл')
        self.compose = ['docker', 'compose', '--project-directory', str(self.project), '-f', str(compose[0])]
        self.state_file = self.primary / 'backup-runtime.json'
        self.state = {}

    def dc(self, *args, **kwargs):
        """Использует действующий продовый Compose без его изменения"""
        return command(self.compose + list(args), cwd=self.project, **kwargs)

    def pg(self, text, **kwargs):
        """Берёт учётные данные из окружения контейнера postgres"""
        return self.dc('exec', '-T', 'postgres', 'sh', '-c', text, **kwargs)

    def query(self, query):
        """Выполняет только служебный SELECT в рабочей БД"""
        result = self.pg('exec psql -X -qAt -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"',
                         input=query.encode(), stdout=subprocess.PIPE, timeout=30)
        return result.stdout.decode().strip()

    def inspect(self, service):
        """Получает один существующий контейнер сервиса"""
        ids = self.dc('ps', '--all', '-q', service, stdout=subprocess.PIPE, timeout=30).stdout.decode().split()
        require(len(ids) == 1, 'Ожидался один контейнер: ' + service)
        return json.loads(command(['docker', 'inspect', ids[0]], stdout=subprocess.PIPE, timeout=30).stdout)[0]

    def check(self):
        """Проверяет окружение без остановки приложения и изменения данных"""
        ZoneInfo('Asia/Yekaterinburg')
        context = json.loads(command(['docker', 'context', 'inspect'], stdout=subprocess.PIPE, timeout=30).stdout)[0]
        require(context['Endpoints']['docker']['Host'].startswith('unix://'), 'Нужен локальный Docker сервера')
        services = self.dc('config', '--services', stdout=subprocess.PIPE, timeout=30).stdout.decode().split()
        require(all(s in services for s in ('postgres', 'fastapi_app', 'nginx')), 'Не найдены обязательные сервисы')
        self.containers = {name: self.inspect(name) for name in ('postgres', 'nginx', 'fastapi_app', 'filebrowser', 'pgadmin') if name in services}
        require(self.containers['postgres']['State']['Running'], 'Postgres должен работать')
        browser = self.containers.get('filebrowser')
        self.mirror_owner = (self.config.get('mirror_uid', 0), self.config.get('mirror_gid', 0))
        if browser and browser['State']['Running']:
            status = Path('/proc/' + str(browser['State']['Pid']) + '/status').read_text().splitlines()
            uid = int(next(line for line in status if line.startswith('Uid:')).split()[4])
            gid = int(next(line for line in status if line.startswith('Gid:')).split()[4])
            self.mirror_owner = uid, gid
            self.config.update(mirror_uid=uid, mirror_gid=gid)
        backend = self.containers['fastapi_app']
        require(not backend['HostConfig'].get('PortBindings') and backend['HostConfig'].get('NetworkMode') != 'host', 'Прямой внешний порт backend мешает закрыть запись через nginx')
        env = dict(value.split('=', 1) for value in backend['Config']['Env'] if '=' in value)
        require(env.get('DB_NAME') == self.config['database'] and env.get('DB_HOST') in ('postgres', 'postgres_db'), 'Backend использует другую БД')
        configured = PurePosixPath(env.get('FILE_STORAGE_PATH', './storage'))
        if not configured.is_absolute():
            configured = PurePosixPath(backend['Config'].get('WorkingDir') or '/') / configured
        require(configured == PurePosixPath('/app/storage'), 'Ожидался storage в /app/storage')
        mounts = [m for m in backend['Mounts'] if m['Destination'] == '/app/storage' and m['Type'] == 'bind']
        require(len(mounts) == 1 and Path(mounts[0]['Source']).resolve() == self.storage, 'Не совпала привязка storage')
        require(self.query('SELECT current_database();') == self.config['database'], 'POSTGRES_DB не совпала с рабочей БД')
        self.db_size = int(self.query('SELECT pg_database_size(current_database());'))
        _, self.storage_size = inventory(self.storage)
        for target in (self.primary, self.mirror):
            parent = target
            while not parent.exists():
                parent = parent.parent
            require(parent.is_dir(), 'Неправильный путь копий')
        log('Проверено: БД ' + self.config['database'] + ' целиком, storage целиком')
        log('Размер БД: ' + str(round(self.db_size / 1024**2, 1)) + ' МиБ; storage без повторного учёта жёстких ссылок: ' + str(round(self.storage_size / 1024**2, 1)) + ' МиБ')

    def directories(self):
        """Создаёт только выделенные закрытые каталоги копий"""
        for path in (self.primary, self.mirror):
            path.mkdir(parents=True, exist_ok=True, mode=0o700)
            require(not path.is_symlink(), 'Ссылка вместо каталога копий')
        self.mirror_access(self.mirror)
        primary_need = 3 * (self.storage_size + self.db_size) + 256 * 1024**2
        mirror_need = self.storage_size + self.db_size + 256 * 1024**2
        if self.primary.stat().st_dev == self.mirror.stat().st_dev:
            primary_need += mirror_need
            log('Обе копии находятся на одном файловом томе; от отказа этого тома они не защищают')
        require(shutil.disk_usage(self.primary).free > primary_need and shutil.disk_usage(self.mirror).free > mirror_need, 'Недостаточно места; старые копии сохранены')

    def mirror_access(self, path):
        """Даёт доступ к дублю пользователю действующего File Browser"""
        owner = getattr(self, 'mirror_owner', (os.geteuid(), os.getegid()))
        info = path.stat()
        if (info.st_uid, info.st_gid) != owner:
            os.chown(path, *owner)
        os.chmod(path, 0o700 if path.is_dir() else 0o600)

    def save_state(self):
        """Фиксирует состояние перед остановкой и после возврата сервисов"""
        save_json(self.state_file, self.state)

    def pause(self, stage):
        """Закрывает вход и останавливает известные источники записи"""
        order = ('nginx', 'fastapi_app', 'filebrowser', 'pgadmin')
        running = [name for name in order if name in self.containers and self.containers[name]['State']['Running']]
        previous = {key: self.state[key] for key in ('last_success', 'archive') if key in self.state}
        self.state = {**previous, 'snapshot_started_at': dt.datetime.now(dt.timezone.utc).isoformat(), 'format': FORMAT, 'pending': True, 'stage': str(stage), 'running': running,
                      'containers': {k: v['Id'] for k, v in self.containers.items()}, 'phase': 'capturing'}
        self.save_state()
        if running:
            self.dc('stop', '--timeout', '30', *running, timeout=180)

    def capture(self, stage):
        """Создаёт неподвижные снимки БД и storage до возобновления записи"""
        before, _ = inventory(self.storage)
        with (stage / 'database.dump').open('wb') as stream:
            self.pg('exec pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom', stdout=stream, timeout=21600)
            stream.flush(); os.fsync(stream.fileno())
        with tarfile.open(stage / 'storage.tar', 'w', dereference=False) as archive:
            archive.add(self.storage, arcname='storage')
        with (stage / 'storage.tar').open('rb') as stream:
            os.fsync(stream.fileno())
        require(inventory(self.storage)[0] == before, 'Во время копирования изменился storage')
        for service, original in self.containers.items():
            current = self.inspect(service)
            require(current['Id'] == original['Id'] and current['State']['StartedAt'] == original['State']['StartedAt'], 'Контейнер перезапустился во время снимка')
            if service in self.state['running']:
                require(not current['State']['Running'], 'Во время снимка возобновилась запись')
        self.state['phase'] = 'captured'; self.save_state()
        return len(before)

    def resume(self):
        """Возвращает только ранее работавшие контейнеры без их пересоздания"""
        if not self.state.get('pending'):
            return
        deadline = time.monotonic() + 60
        while True:
            try:
                require(self.query('SELECT 1;') == '1', 'Postgres не готов')
                break
            except (RuntimeError, subprocess.SubprocessError):
                require(time.monotonic() < deadline, 'Postgres не готов; восстановление будет повторено')
                time.sleep(3)
        for service in ('fastapi_app', 'pgadmin', 'filebrowser', 'nginx'):
            if service not in self.state['running']:
                continue
            current = self.inspect(service)
            require(current['Id'] == self.state['containers'][service], 'Контейнер заменён извне: ' + service)
            if not current['State']['Running']:
                command(['docker', 'start', current['Id']], stdout=subprocess.DEVNULL, timeout=60)
            if service == 'fastapi_app':
                deadline = time.monotonic() + 90
                check = "import urllib.request; assert urllib.request.urlopen('http://127.0.0.1:8000/openapi.json',timeout=5).status==200"
                while True:
                    result = subprocess.run(self.compose + ['exec', '-T', 'fastapi_app', 'python', '-c', check], cwd=self.project, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15)
                    if result.returncode == 0:
                        break
                    require(time.monotonic() < deadline, 'Backend не готов; восстановление будет повторено')
                    time.sleep(3)
        self.state['pending'] = False; self.state['phase'] = 'resumed'; self.save_state()
        log('Приложение снова доступно')

    def cleanup_stage(self):
        """Удаляет только собственные незавершённые временные файлы"""
        value = self.state.get('stage')
        if value:
            path = Path(value)
            require(path.parent == self.primary and re.fullmatch(r'\.building-[0-9a-f]{32}', path.name), 'Неожиданный путь временных файлов')
            if path.exists():
                require(not path.is_symlink(), 'Ссылка вместо временной папки')
                shutil.rmtree(path)
        temporary = self.state.get('mirror_temporary')
        if temporary:
            path = Path(temporary)
            require(path.parent == self.mirror and re.fullmatch(r'\.copy-[0-9a-f]{32}', path.name), 'Неожиданный временный дубль')
            path.unlink(missing_ok=True)
        self.state['stage'] = None; self.state['mirror_temporary'] = None
        self.save_state()

    def recover(self):
        """Возобновляет работу после прерывания задания или перезапуска сервера"""
        if not self.state_file.exists():
            return
        self.state = json.loads(self.state_file.read_text())
        require(self.state.get('format') == FORMAT, 'Неизвестное состояние предыдущего задания')
        self.resume()
        self.cleanup_stage()

    def validate_storage(self, path, expected):
        """Полностью читает сжатый архив и проверяет имена и жёсткие ссылки"""
        seen = set()
        with gzip.open(path, 'rb') as zipped:
            with tarfile.open(fileobj=zipped, mode='r|') as archive:
                for member in archive:
                    parts = PurePosixPath(member.name).parts
                    require(parts and parts[0] == 'storage' and '..' not in parts and not member.name.startswith('/'), 'Недопустимый путь в архиве storage')
                    require(member.name not in seen, 'Повтор имени в архиве storage')
                    if member.isreg():
                        stream = archive.extractfile(member)
                        stream_hash(stream)
                    elif member.islnk():
                        require(member.linkname in seen, 'Потеряна цель жёсткой ссылки')
                    else:
                        require(member.isdir() or member.issym(), 'Неизвестный тип файла в storage')
                    seen.add(member.name)
            while zipped.read(1024 * 1024):
                pass
        require(len(seen) == expected, 'Не совпало количество записей storage')

    def publish(self, stage, manifest, name):
        """Публикует проверенный полный архив в двух независимых файлах"""
        package = stage / 'package.tar'
        with tarfile.open(package, 'w') as archive:
            for item in ('database.dump', 'storage.tar.gz', 'manifest.json'):
                archive.add(stage / item, arcname=item)
        expected = {item: checksum(stage / item) for item in ('database.dump', 'storage.tar.gz', 'manifest.json')}
        with tarfile.open(package, 'r:') as archive:
            require(set(archive.getnames()) == set(expected) and len(archive.getmembers()) == 3, 'Неполный пакет')
            for member in archive:
                require(member.isreg() and stream_hash(archive.extractfile(member)) == expected[member.name], 'Не совпала проверка содержимого пакета')
        with package.open('rb') as stream:
            os.fsync(stream.fileno())
        digest = checksum(package)
        target = self.primary / name
        os.link(package, target); sync_dir(self.primary)
        atomic(target.with_name(name + '.sha256'), (digest + '  ' + name + '\n').encode())
        temporary = self.mirror / ('.copy-' + uuid.uuid4().hex)
        self.state['mirror_temporary'] = str(temporary); self.save_state()
        with package.open('rb') as source, temporary.open('xb') as dest:
            shutil.copyfileobj(source, dest, 1024 * 1024)
            dest.flush(); os.fsync(dest.fileno())
        require(checksum(temporary) == digest, 'Дубль не совпал с основной копией')
        self.mirror_access(temporary)
        mirror = self.mirror / name
        os.link(temporary, mirror); sync_dir(self.mirror)
        temporary.unlink(); sync_dir(self.mirror)
        atomic(mirror.with_name(name + '.sha256'), (digest + '  ' + name + '\n').encode())
        self.mirror_access(mirror.with_name(name + '.sha256'))
        self.state['mirror_temporary'] = None
        self.state['last_success'] = manifest['created_at']; self.state['archive'] = name
        self.state['phase'] = 'completed'; self.save_state()
        return target, mirror

    def expired(self, path, cutoff):
        """Определяет принадлежность и возраст только собственных готовых копий"""
        if not NAME.fullmatch(path.name) or path.is_symlink() or not path.is_file():
            return False
        sidecar = path.with_name(path.name + '.sha256')
        if not sidecar.is_file() or sidecar.is_symlink():
            return False
        try:
            with tarfile.open(path, 'r:') as archive:
                member = archive.getmember('manifest.json')
                if not member.isreg() or member.size > 65536:
                    return False
                manifest = json.load(archive.extractfile(member))
            if not isinstance(manifest, dict):
                return False
            date = dt.datetime.fromisoformat(manifest['created_at'])
            if not (manifest.get('format') == FORMAT and manifest.get('database') == self.config['database'] and manifest.get('project') == str(self.project) and date.tzinfo and date < cutoff):
                return False
            return sidecar.read_text().strip() == checksum(path) + '  ' + path.name
        except (OSError, ValueError, KeyError, tarfile.TarError):
            return False

    def prune(self, current):
        """Удаляет копии старше 30 суток только после проверки новой пары"""
        a, b = current
        require(a.is_file() and b.is_file() and checksum(a) == checksum(b), 'Перед очисткой пропала новая копия')
        cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=30)
        for directory in (self.primary, self.mirror):
            for path in directory.iterdir():
                if path not in current and self.expired(path, cutoff):
                    path.unlink(); path.with_name(path.name + '.sha256').unlink(); sync_dir(directory)
                    log('Удалена просроченная копия: ' + path.name)

    def prune_saved(self):
        """Проверяет последнюю успешную пару перед ежедневной очисткой"""
        self.recover()
        name = self.state.get('archive')
        if not name:
            log('Очистка пропущена: успешного бэкапа пока нет')
            return
        require(NAME.fullmatch(name), 'Неожиданное имя последней копии')
        copies = self.primary / name, self.mirror / name
        require(all(path.is_file() and not path.is_symlink() for path in copies), 'Последняя пара неполна; старые копии сохранены')
        digest = checksum(copies[0])
        require(checksum(copies[1]) == digest, 'Последняя пара отличается; старые копии сохранены')
        for path in copies:
            require(path.with_name(name + '.sha256').read_text().strip() == digest + '  ' + name, 'Не совпала контрольная сумма; очистка отменена')
        self.prune(copies)

    def run(self):
        """Делает один полный бэкап и сохраняет старые копии при любой ошибке"""
        self.recover()
        self.check(); self.directories()
        stage = self.primary / ('.building-' + uuid.uuid4().hex); stage.mkdir(mode=0o700)
        started = time.monotonic()
        try:
            try:
                self.pause(stage)
                entries = self.capture(stage)
            finally:
                self.resume()
            downtime = round(time.monotonic() - started, 1)
            log('Снимок готов. Перерыв: ' + str(downtime) + ' с. Сжатие и проверка идут при работающем приложении')
            with (stage / 'database.dump').open('rb') as stream:
                self.pg('exec pg_restore --exit-on-error --file=/dev/null', stdin=stream, stdout=subprocess.DEVNULL, timeout=21600)
            with (stage / 'storage.tar').open('rb') as source, (stage / 'storage.tar.gz').open('wb') as dest:
                with gzip.GzipFile(fileobj=dest, mode='wb', compresslevel=6, mtime=0) as zipped:
                    shutil.copyfileobj(source, zipped, 1024 * 1024)
                dest.flush(); os.fsync(dest.fileno())
            self.validate_storage(stage / 'storage.tar.gz', entries)
            created = dt.datetime.now(dt.timezone.utc)
            manifest = {'format': FORMAT, 'created_at': created.isoformat(), 'snapshot_started_at': self.state['snapshot_started_at'], 'project': str(self.project), 'database': self.config['database'],
                        'postgres_version': self.query('SHOW server_version;'), 'storage_entries': entries, 'pause_seconds': downtime,
                        'files': {name: {'sha256': checksum(stage / name), 'bytes': (stage / name).stat().st_size} for name in ('database.dump', 'storage.tar.gz')}}
            save_json(stage / 'manifest.json', manifest)
            name = 'complaint-backup-' + created.astimezone(ZoneInfo('Asia/Yekaterinburg')).strftime('%Y%m%d-%H%M%S-') + uuid.uuid4().hex[:12] + '.tar'
            copies = self.publish(stage, manifest, name)
            self.prune(copies)
            log('Успешно: ' + str(copies[0]) + ' и ' + str(copies[1]))
        finally:
            if not self.state.get('pending'):
                self.cleanup_stage()


def unit_files():
    """Описывает серверное расписание и восстановление после прерывания"""
    executable = json.dumps(str(Path(sys.executable).resolve())) + ' ' + str(PROGRAM)
    header = '# Managed by complaint-app-backup\n'
    service = header + '''[Unit]
Description=Backup complaint database and storage
OnFailure=complaint-app-backup-recover.service
After=docker.service network-online.target

[Service]
Type=oneshot
User=root
UMask=0077
Nice=10
IOSchedulingClass=best-effort
IOSchedulingPriority=7
TimeoutStartSec=6h
TimeoutStopSec=300
''' + 'ExecStart=' + executable + ' run\nExecStopPost=' + executable + ' recover\n'
    timer = header + '''[Unit]
Description=Weekly complaint backup Friday 03:00 Yekaterinburg

[Timer]
OnCalendar=Fri *-*-* 03:00:00 Asia/Yekaterinburg
AccuracySec=1s
Persistent=false
Unit=complaint-app-backup.service

[Install]
WantedBy=timers.target
'''
    recover = header + '''[Unit]
Description=Resume complaint services after interrupted backup
After=docker.service network-online.target
StartLimitIntervalSec=0

[Service]
Type=oneshot
User=root
UMask=0077
Restart=on-failure
RestartSec=30
TimeoutStartSec=300
''' + 'ExecStart=' + executable + ' recover\n\n[Install]\nWantedBy=multi-user.target\n'
    prune = header + '[Unit]\nDescription=Expire complaint backups older than 30 days\n\n[Service]\nType=oneshot\nUser=root\nUMask=0077\nNice=10\nExecStart=' + executable + ' prune\n'
    prune_timer = header + '[Unit]\nDescription=Daily complaint backup retention check\n\n[Timer]\nOnCalendar=*-*-* 04:00:00 Asia/Yekaterinburg\nPersistent=false\nUnit=complaint-app-backup-prune.service\n\n[Install]\nWantedBy=timers.target\n'
    return {'complaint-app-backup.service': service, 'complaint-app-backup.timer': timer,
            'complaint-app-backup-recover.service': recover, 'complaint-app-backup-prune.service': prune,
            'complaint-app-backup-prune.timer': prune_timer}


def ignore_changes(backup):
    """Добавляет копии в исключения Docker, сохраняя существующие правила"""
    config = json.loads(backup.dc('config', '--format', 'json', stdout=subprocess.PIPE, timeout=30).stdout)
    result = {}
    for service in config['services'].values():
        build = service.get('build')
        if not isinstance(build, dict):
            continue
        context = Path(build['context']).resolve()
        if not backup.mirror.is_relative_to(context):
            continue
        require(not build.get('dockerfile_inline'), 'Для этого контекста нужен обычный Dockerfile')
        relative = backup.mirror.relative_to(context).as_posix()
        require(relative != '.' and not any(c in relative for c in '*?[]!\n\r\\'), 'Недопустимый путь дублей')
        dockerfile = Path(build.get('dockerfile', 'Dockerfile'))
        if not dockerfile.is_absolute():
            dockerfile = context / dockerfile
        targets = [context / '.dockerignore']
        specific = Path(str(dockerfile) + '.dockerignore')
        if specific.exists():
            targets.append(specific)
        for target in targets:
            require(target.resolve().is_relative_to(backup.project) and not target.is_symlink(), 'Неожиданный файл исключений Docker')
            before = target.read_text() if target.exists() else ''
            line = '/' + relative + '/'
            block = '\n\n# complaint-app-backup\n' + line + '\n'
            updated = before.replace(block, '').rstrip('\n') + block
            if updated != before:
                result[target] = updated.encode()
    return result


def install(backup):
    """Устанавливает один скрипт и серверные задания с возвратом файлов при ошибке"""
    require(Path('/run/systemd/system').is_dir() and shutil.which('systemctl') and shutil.which('systemd-analyze'), 'На сервере нужен systemd; установка не выполнена')
    backup.check(); backup.directories()
    command(['systemd-analyze', 'calendar', CALENDAR], stdout=subprocess.PIPE, timeout=30)
    require(not backup.state_file.exists() or not json.loads(backup.state_file.read_text()).get('pending'), 'Сначала выполните recover для предыдущего бэкапа')
    active = subprocess.run(['systemctl', 'is-active', '--quiet', 'complaint-app-backup.service']).returncode == 0
    require(not active, 'Сейчас уже выполняется резервное копирование')
    header = '# Managed by complaint-app-backup'
    units = unit_files()
    for name in units:
        path = UNITS / name
        require(not path.is_symlink() and (not path.exists() or path.read_text().startswith(header)), 'Существует чужой файл: ' + str(path))
    require(not PROGRAM.is_symlink() and (not PROGRAM.exists() or header in PROGRAM.read_text().splitlines()[:3]), 'Существует чужая программа: ' + str(PROGRAM))
    if CONFIG.exists():
        require(not CONFIG.is_symlink() and json.loads(CONFIG.read_text()).get('format') == FORMAT, 'Существует чужой файл настроек')
    script = Path(__file__).read_bytes()
    if header.encode() not in script.splitlines()[:3]:
        script = script.replace(b'\n', b'\n' + header.encode() + b'\n', 1)
    changes = {PROGRAM: (script, 0o750), CONFIG: (json.dumps(backup.config, ensure_ascii=False, indent=2).encode(), 0o600)}
    changes.update({UNITS / name: (text.encode(), 0o644) for name, text in units.items()})
    for path, value in ignore_changes(backup).items():
        changes[path] = (value, stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o644)
    previous = {}
    for path in changes:
        require(not path.is_symlink(), 'Ссылка вместо устанавливаемого файла')
        previous[path] = (path.read_bytes(), path.stat()) if path.exists() else None
    timer_states = {}
    for name in ('complaint-app-backup.timer', 'complaint-app-backup-prune.timer'):
        timer_states[name] = {
            'enabled': subprocess.run(['systemctl', 'is-enabled', '--quiet', name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0,
            'active': subprocess.run(['systemctl', 'is-active', '--quiet', name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0}
    recover_enabled = subprocess.run(['systemctl', 'is-enabled', '--quiet', 'complaint-app-backup-recover.service'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
    installed = []
    try:
        for name, previous_state in timer_states.items():
            if previous_state['active']:
                command(['systemctl', 'stop', name], stdout=subprocess.DEVNULL, timeout=60)
        for path, (content, mode) in changes.items():
            require(path.parent.is_dir(), 'Не найдена системная папка: ' + str(path.parent))
            atomic(path, content, mode); installed.append(path)
        command(['systemd-analyze', 'verify'] + [str(UNITS / name) for name in units], stdout=subprocess.PIPE, timeout=60)
        command(['systemctl', 'daemon-reload'], stdout=subprocess.DEVNULL, timeout=60)
        command(['systemctl', 'enable', 'complaint-app-backup-recover.service'], stdout=subprocess.DEVNULL, timeout=60)
        for name in timer_states:
            command(['systemctl', 'enable', '--now', name], stdout=subprocess.DEVNULL, timeout=60)
    except BaseException:
        for name in timer_states:
            subprocess.run(['systemctl', 'stop', name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if not recover_enabled:
            subprocess.run(['systemctl', 'disable', 'complaint-app-backup-recover.service'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for name, previous_state in timer_states.items():
            if not previous_state['enabled']:
                subprocess.run(['systemctl', 'disable', name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for path in reversed(installed):
            saved = previous[path]
            if saved is None:
                path.unlink(missing_ok=True)
            else:
                atomic(path, saved[0], stat.S_IMODE(saved[1].st_mode))
                os.chown(path, saved[1].st_uid, saved[1].st_gid)
        subprocess.run(['systemctl', 'daemon-reload'])
        for name, previous_state in timer_states.items():
            if previous_state['active']:
                subprocess.run(['systemctl', 'start', name])
        raise
    log('Установлено: пятница 03:00 Asia/Yekaterinburg, хранение 30 суток')
    log('Основная копия: ' + str(backup.primary) + '; дубль: ' + str(backup.mirror))
    log('Установка не запускает бэкап немедленно и не останавливает приложение')
    command(['systemctl', 'list-timers', '--all', 'complaint-app-backup.timer', 'complaint-app-backup-prune.timer'], stdout=None, timeout=30)


def main():
    """Выполняет проверку, установку, ручной запуск или восстановление сервисов"""
    require(sys.version_info >= (3, 9), 'Нужен Python 3.9 или новее')
    require(os.geteuid() == 0, 'Запустите через sudo')
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('check', 'install', 'run', 'recover', 'prune', 'status'))
    parser.add_argument('--project'); parser.add_argument('--database')
    parser.add_argument('--primary'); parser.add_argument('--mirror')
    args = parser.parse_args()
    config = dict(DEFAULTS)
    if CONFIG.exists():
        require(not CONFIG.is_symlink(), 'Настройки не должны быть ссылкой')
        config.update(json.loads(CONFIG.read_text()))
    for name in ('project', 'database', 'primary', 'mirror'):
        value = getattr(args, name)
        if value:
            config[name] = value
    backup = Backup(config)
    if args.action == 'status':
        command(['systemctl', 'list-timers', '--all', 'complaint-app-backup.timer', 'complaint-app-backup-prune.timer'], stdout=None, timeout=30)
        if backup.state_file.exists():
            state = json.loads(backup.state_file.read_text())
            log('Этап: ' + state.get('phase', '?') + '; последний успешный архив: ' + str(state.get('archive', 'ещё нет')))
        return
    runtime = Path('/run/complaint-app-backup')
    runtime.mkdir(mode=0o700, exist_ok=True)
    require(not runtime.is_symlink(), 'Ссылка вместо служебной папки')
    with (runtime / 'lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError('Другое задание резервного копирования уже выполняется')
        if args.action == 'check':
            backup.check()
        elif args.action == 'install':
            install(backup)
        elif args.action == 'recover':
            backup.recover()
        elif args.action == 'prune':
            backup.prune_saved()
        else:
            signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))
            backup.run()


if __name__ == '__main__':
    try:
        main()
    except (Exception, KeyboardInterrupt) as error:
        log('Ошибка резервного копирования: ' + str(error))
        sys.exit(1)
