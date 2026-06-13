import { useState, type CSSProperties } from "react";
import { type LucideIcon } from "lucide-react";
import { ASSETS } from "@/lib/constants";
import { LogoMark } from "../LogoMark";

export function SafeImage({
  src,
  alt,
  className,
  style,
  decorative = false,
  fallbackIcon: FallbackIcon,
}: {
  src: string;
  alt: string;
  className?: string;
  style?: CSSProperties;
  decorative?: boolean;
  fallbackIcon?: LucideIcon;
}) {
  const [failed, setFailed] = useState(false);

  if (failed) {
    if (FallbackIcon) {
      return (
        <div
          className={`flex items-center justify-center bg-[oklch(0.18_0_0)] ${className ?? ""}`}
          style={style}
          aria-hidden={decorative}
        >
          <FallbackIcon className="w-8 h-8 text-teal opacity-60" />
        </div>
      );
    }
    return (
      <div
        className={`bg-[oklch(0.18_0_0)] ${className ?? ""}`}
        style={style}
        aria-hidden={decorative}
      />
    );
  }

  return (
    <img
      src={src}
      alt={decorative ? "" : alt}
      aria-hidden={decorative || undefined}
      loading="lazy"
      className={className}
      style={style}
      onError={() => setFailed(true)}
    />
  );
}

export function Logo() {
  return <LogoMark style={{ fontSize: "1.25rem", lineHeight: 1.2 }} />;
}

export function NoiseOverlay() {
  const [failed, setFailed] = useState(false);
  if (failed) return null;
  return (
    <img
      src={ASSETS.noise}
      alt=""
      aria-hidden
      loading="lazy"
      className="absolute inset-0 w-full h-full object-cover opacity-[0.12] mix-blend-overlay pointer-events-none"
      style={{ zIndex: 1 }}
      onError={() => setFailed(true)}
    />
  );
}
