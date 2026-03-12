import { useEffect } from "react";

let lockCount = 0;
let originalOverflow = "";
let originalPaddingRight = "";

export const useBodyScrollLock = (isLocked = true) => {
  useEffect(() => {
    if (isLocked) {
      if (lockCount === 0) {
        const body = document.body;
        originalOverflow =
          body.style.overflow || window.getComputedStyle(body).overflow;

        const scrollbarWidth =
          window.innerWidth - document.documentElement.clientWidth;
        if (scrollbarWidth > 0) {
          originalPaddingRight =
            body.style.paddingRight ||
            window.getComputedStyle(body).paddingRight;
          body.style.paddingRight = `${scrollbarWidth}px`;
        }

        body.style.overflow = "hidden";
      }
      lockCount++;
    }

    const cleanup = () => {
      if (isLocked && lockCount > 0) {
        lockCount--;
        if (lockCount === 0) {
          document.body.style.overflow = originalOverflow || "";
          document.body.style.paddingRight = originalPaddingRight || "";
        }
      }
    };

    // Принудительное восстановление при обновлении страницы
    const handleBeforeUnload = () => {
      if (lockCount > 0) {
        document.body.style.overflow = originalOverflow || "";
        document.body.style.paddingRight = originalPaddingRight || "";
      }
    };

    window.addEventListener("beforeunload", handleBeforeUnload);

    return () => {
      cleanup();
      window.removeEventListener("beforeunload", handleBeforeUnload);
    };
  }, [isLocked]);
};
