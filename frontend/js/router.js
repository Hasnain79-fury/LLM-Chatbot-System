/* ═══════════════════════════════════════════════════════════════════════════
   Simple hash-based SPA Router
   ═══════════════════════════════════════════════════════════════════════════ */

const routes = {};

export function registerRoute(hash, renderFn) {
  routes[hash] = renderFn;
}

export function navigate(hash) {
  window.location.hash = hash;
}

export function currentRoute() {
  return window.location.hash || '#/login';
}

export function startRouter() {
  const handleRoute = () => {
    const hash = currentRoute();
    const renderFn = routes[hash];
    if (renderFn) {
      renderFn();
    } else {
      // Default: redirect to login
      navigate('#/login');
    }
  };

  window.addEventListener('hashchange', handleRoute);
  handleRoute(); // initial render
}
