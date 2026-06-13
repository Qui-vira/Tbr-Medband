export function getParticleCount(requested: number): number {
  if (typeof window === "undefined") return requested;

  if (window.innerWidth < 768) {
    return Math.floor(requested * 0.3);
  }

  if (navigator.hardwareConcurrency <= 4) {
    return Math.floor(requested * 0.5);
  }

  return requested;
}
