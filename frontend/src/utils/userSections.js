/** Проверяет возможность назначения ответственным в выбранном направлении */
export const canAssignCaseOwner = (user, direction) =>
  !!user &&
  user.is_active !== false &&
  ["editor", "superadmin"].includes(user.role) &&
  (user.role === "superadmin" || (user.direction || "loco") === direction);

/** Выбирает список текущего раздела или стартовый раздел пользователя */
export const getHomeSection = (user, location) => {
  if (user?.restricted_access) return "/dashboard";
  const currentSection = getLocationSection(location);
  if (currentSection) return currentSection;
  if (user?.role === "viewer") {
    try {
      const path = localStorage.getItem(`last-section:${user.id}`);
      if (["/train", "/dashboard"].includes(path)) return path;
    } catch {
      /* Хранилище браузера может быть недоступно */
    }
    return "/dashboard";
  }
  return user?.direction === "train" ? "/train" : "/dashboard";
};

/** Определяет список, к которому относится текущая страница */
const getLocationSection = (location) => {
  const path = location?.pathname;
  if (path === "/train" || path?.startsWith("/train/")) return "/train";
  if (["/dashboard", "/product-passports", "/equipment-management"].includes(path))
    return "/dashboard";
  if (path === "/omega-stock") {
    const returnTo = location.state?.returnTo;
    if (["/train", "/dashboard"].includes(returnTo)) return returnTo;
  }
  return null;
};

/** Запоминает раздел просмотра отдельно для каждой учётной записи */
export const rememberViewerSection = (user, location) => {
  if (user?.role !== "viewer" || user.restricted_access) return;
  const path = getLocationSection(location);
  if (!path) return;
  try {
    localStorage.setItem(`last-section:${user.id}`, path);
  } catch {
    /* Хранилище браузера может быть недоступно */
  }
};
