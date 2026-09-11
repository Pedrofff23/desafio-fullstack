import { nextTick } from 'vue';

type ElementLike = HTMLElement | { $el?: unknown } | null | undefined;

function resolveElement(target?: ElementLike | string): HTMLElement | null {
  if (!target) return null;
  if (typeof target === 'string') {
    return document.querySelector<HTMLElement>(target);
  }
  if (target instanceof HTMLElement) {
    return target;
  }
  if (typeof target === 'object' && target !== null && '$el' in target) {
    const el = (target as { $el?: unknown }).$el;
    if (el instanceof HTMLElement) {
      return el;
    }
  }
  return null;
}

/**
 * Rola suavemente a tela ou o modal ativo até o elemento de alerta de erro (v-alert).
 * Aplica um destaque pulsante sutil para direcionar a atenção visual do usuário.
 */
export async function scrollToError(preferredTarget?: ElementLike | string): Promise<void> {
  await nextTick();
  requestAnimationFrame(() => {
    let el = resolveElement(preferredTarget);

    if (!el) {
      // Procura se tem um overlay ativo com alerta de erro
      const activeOverlay = document.querySelector<HTMLElement>('.v-overlay--active .v-overlay__content');
      if (activeOverlay) {
        el = activeOverlay.querySelector<HTMLElement>(
          '.v-alert.bg-error, .v-alert--type-error, .v-alert[type="error"], [data-alert="error"], .v-alert'
        );
      }
    }

    if (!el) {
      // Procura alerta de erro na página principal
      el = document.querySelector<HTMLElement>(
        '.v-alert.bg-error, .v-alert--type-error, .v-alert[type="error"], [data-alert="error"], .v-alert'
      );
    }

    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'center' });
      el.classList.remove('error-alert-pulse');
      void el.offsetWidth;
      el.classList.add('error-alert-pulse');
    } else {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  });
}

