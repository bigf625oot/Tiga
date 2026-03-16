if (typeof window !== 'undefined' && typeof window.matchMedia !== 'function') {
  window.matchMedia = (query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  })
}

if (typeof HTMLCanvasElement !== 'undefined') {
  HTMLCanvasElement.prototype.getContext = function getContext() {
    const canvas = this
    const ctx = { canvas }
    return new Proxy(ctx, {
      get(target, prop) {
        if (prop in target) return target[prop]
        return () => {}
      },
      set(target, prop, value) {
        target[prop] = value
        return true
      },
    })
  }
}
