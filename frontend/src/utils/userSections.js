/** Проверяет возможность назначения ответственным в выбранном направлении */
export const canAssignCaseOwner = (user, direction) =>
  !!user &&
  user.is_active !== false &&
  ["editor", "superadmin"].includes(user.role) &&
  (user.role === "superadmin" || (user.direction || "loco") === direction);

/** Выбирает стартовый раздел, для просмотра восстанавливает последний открытый */
export const getHomeSection = (user) => {
  if (user?.restricted_access) return "/dashboard";
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

/** Запоминает раздел просмотра отдельно для каждой учётной записи */
export const rememberViewerSection = (user, location) => {
  if (user?.role !== "viewer" || user.restricted_access) return;
  const path = location.pathname.startsWith("/train")
    ? "/train"
    : ["/dashboard", "/product-passports", "/equipment-management"].includes(
          location.pathname,
        )
      ? "/dashboard"
      : location.pathname === "/omega-stock"
        ? location.state?.returnTo
        : null;
  if (!["/train", "/dashboard"].includes(path)) return;
  try {
    localStorage.setItem(`last-section:${user.id}`, path);
  } catch {
    /* Хранилище браузера может быть недоступно */
  }
};
