import { useEffect, useRef, useState, type ReactNode } from "react";

type ViewportSectionProps = {
  children: ReactNode;
  className?: string;
  minHeight?: string;
};

export function ViewportSection({
  children,
  className = "",
  minHeight = "min-h-screen",
}: ViewportSectionProps) {
  const ref = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const node = ref.current;
    if (!node) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true);
          observer.disconnect();
        }
      },
      { rootMargin: "400px 0px" },
    );

    observer.observe(node);
    return () => observer.disconnect();
  }, []);

  return (
    <div ref={ref} className={className}>
      {visible ? (
        children
      ) : (
        <div className={`${minHeight} bg-[#0A0F1A]`} aria-hidden />
      )}
    </div>
  );
}

export function SectionFallback() {
  return <div className="min-h-screen bg-[#0A0F1A]" aria-hidden />;
}
