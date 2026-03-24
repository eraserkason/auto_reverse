import { nextTick, ref } from 'vue';

type FocusableTarget = {
  focus?: () => void;
};

export interface BrowserTaskObserverOptions {
  topbarRef: { value: { observerToggleButtonRef: FocusableTarget | null } | null };
  taskSystemRef: { value: { observerPanelRef: HTMLElement | null; observerCloseButtonRef: FocusableTarget | null; modelSelectRef?: FocusableTarget | null } | null };
  composerRef: { value: { promptTextareaRef: FocusableTarget | null } | null };
}

export function useBrowserTaskObserver(opts: BrowserTaskObserverOptions) {
  const { topbarRef, taskSystemRef, composerRef } = opts;

  const observerOpen = ref(false);
  const isInlineTaskSystem = ref(false);

  let mediaQueryList: MediaQueryList | null = null;
  let mediaQueryHandler: ((event: MediaQueryListEvent) => void) | null = null;
  let observerHtmlOverflow = '';
  let observerBodyOverflow = '';
  let lastFocusedElementBeforeObserverOpen: HTMLElement | null = null;

  function lockObserverBodyScroll(): void {
    observerHtmlOverflow = document.documentElement.style.overflow;
    observerBodyOverflow = document.body.style.overflow;
    document.documentElement.style.overflow = 'hidden';
    document.body.style.overflow = 'hidden';
  }

  function unlockObserverBodyScroll(): void {
    document.documentElement.style.overflow = observerHtmlOverflow;
    document.body.style.overflow = observerBodyOverflow;
    observerHtmlOverflow = '';
    observerBodyOverflow = '';
  }

  function getObserverFocusableElements(): HTMLElement[] {
    const panel = (taskSystemRef.value?.observerPanelRef as HTMLElement | null | undefined) ?? null;
    if (!panel) {
      return [];
    }
    return Array.from(
      panel.querySelectorAll<HTMLElement>(
        'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), summary, [tabindex]:not([tabindex="-1"])',
      ),
    ).filter((el: HTMLElement) => el.getClientRects().length > 0);
  }

  function openObserverPanel(): void {
    if (observerOpen.value) {
      return;
    }
    if (!isInlineTaskSystem.value && document.activeElement instanceof HTMLElement) {
      lastFocusedElementBeforeObserverOpen = document.activeElement;
    }
    observerOpen.value = true;
  }

  function closeObserverPanel(returnFocus = true): void {
    if (!observerOpen.value) {
      return;
    }
    observerOpen.value = false;
    if (!isInlineTaskSystem.value && returnFocus) {
      const focusTarget: HTMLElement | null = lastFocusedElementBeforeObserverOpen?.isConnected
        ? lastFocusedElementBeforeObserverOpen
        : null;
      void nextTick(() => {
        if (focusTarget) {
          focusTarget.focus();
          return;
        }
        topbarRef.value?.observerToggleButtonRef?.focus?.();
      });
    }
    lastFocusedElementBeforeObserverOpen = null;
  }

  function toggleObserverPanel(): void {
    if (observerOpen.value) {
      closeObserverPanel();
      return;
    }
    openObserverPanel();
  }

  function handleObserverPanelKeydown(event: KeyboardEvent): void {
    if (isInlineTaskSystem.value || !observerOpen.value) {
      return;
    }
    if (event.key === 'Escape') {
      event.preventDefault();
      closeObserverPanel();
      return;
    }
    if (event.key !== 'Tab') {
      return;
    }
    const focusableElements = getObserverFocusableElements();
    if (focusableElements.length === 0) {
      event.preventDefault();
      (taskSystemRef.value?.observerPanelRef as HTMLElement | null | undefined)?.focus();
      return;
    }
    const firstElement = focusableElements[0]!;
    const lastElement = focusableElements[focusableElements.length - 1]!;
    const activeElement = document.activeElement as HTMLElement | null;
    if (event.shiftKey && activeElement === firstElement) {
      event.preventDefault();
      lastElement.focus();
      return;
    }
    if (!event.shiftKey && activeElement === lastElement) {
      event.preventDefault();
      firstElement.focus();
    }
  }

  function syncObserverViewport(nextMatches: boolean): void {
    const wasInline = isInlineTaskSystem.value;
    isInlineTaskSystem.value = nextMatches;
    if (!wasInline && nextMatches) {
      unlockObserverBodyScroll();
      observerOpen.value = false;
      return;
    }
    if (wasInline && !nextMatches) {
      unlockObserverBodyScroll();
      observerOpen.value = false;
    }
  }

  function initMediaQuery(): void {
    syncObserverViewport(false);
  }

  function destroyMediaQuery(): void {
    mediaQueryList = null;
    mediaQueryHandler = null;
  }

  function focusPromptComposer(): void {
    void nextTick(() => {
      composerRef.value?.promptTextareaRef?.focus?.();
    });
  }

  function focusModelSelection(): void {
    if (!isInlineTaskSystem.value && !observerOpen.value) {
      openObserverPanel();
    }
    void nextTick(() => {
      window.setTimeout(() => {
        taskSystemRef.value?.modelSelectRef?.focus?.();
      }, 0);
    });
  }

  return {
    observerOpen,
    isInlineTaskSystem,
    lockObserverBodyScroll,
    unlockObserverBodyScroll,
    getObserverFocusableElements,
    openObserverPanel,
    closeObserverPanel,
    toggleObserverPanel,
    handleObserverPanelKeydown,
    syncObserverViewport,
    initMediaQuery,
    destroyMediaQuery,
    focusPromptComposer,
    focusModelSelection,
  };
}

export type BrowserTaskObserverApi = ReturnType<typeof useBrowserTaskObserver>;
