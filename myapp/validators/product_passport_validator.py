from collections import Counter

from myapp.schemas.omega import OmegaPassportNodeData


class ProductPassportValidator:
    """Проверяет данные паспорта перед сохранением в БД"""

    @staticmethod
    def validate_tree(nodes: list[OmegaPassportNodeData], root_code: int) -> None:
        """Проверяет корень, уникальность узлов и наличие родителей"""
        if not nodes:
            raise ValueError("Omega вернула пустое дерево паспорта")

        code_counts = Counter(node.omega_code for node in nodes)
        duplicate_codes = sorted(
            code for code, count in code_counts.items() if count > 1
        )
        if duplicate_codes:
            duplicate_codes_text = ", ".join(map(str, duplicate_codes[:20]))
            raise ValueError(
                "В дереве Omega найдены повторяющиеся узлы: "
                f"{duplicate_codes_text}"
            )

        node_codes = set(code_counts)

        roots = [node for node in nodes if node.parent_omega_code is None]
        if len(roots) != 1 or roots[0].omega_code != root_code:
            raise ValueError("В дереве должен быть один ожидаемый корень")

        for node in nodes:
            if node.omega_code == root_code:
                if node.level != 0:
                    raise ValueError("Корень паспорта должен иметь уровень 0")
                continue
            if node.parent_omega_code not in node_codes:
                raise ValueError(f"У узла {node.omega_code} отсутствует родитель")

        nodes_by_code = {node.omega_code: node for node in nodes}
        for node in nodes:
            visited_codes: set[int] = set()
            current = node

            while current.omega_code != root_code:
                if current.omega_code in visited_codes:
                    raise ValueError(f"В дереве найден цикл у узла {node.omega_code}")

                visited_codes.add(current.omega_code)
                parent = nodes_by_code[current.parent_omega_code]

                if parent.level != current.level - 1:
                    raise ValueError(
                        f"Неверный уровень дерева у узла {current.omega_code}"
                    )

                current = parent
