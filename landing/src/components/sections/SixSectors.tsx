import { useEffect, useState } from "react";
import { m } from "framer-motion";
import { LineField } from "../LineField";
import { StarField } from "../StarField";
import { NoiseOverlay } from "../shared/landing-ui";
import { MATTE } from "@/lib/constants";
import {
  desktopCardIn,
  mobileCardIn,
  viewBlurIn,
  viewFadeIn,
} from "@/lib/motion";
import { SECTORS } from "@/lib/sectors";
import { useIsMobile } from "@/lib/useIsMobile";

const ROADMAP_NAMES = SECTORS.filter((s) => s.roadmap).map((s) => s.name);

export default function SixSectors() {
  const isMobile = useIsMobile();
  const [cycleIndex, setCycleIndex] = useState(0);
  const headingVariants = isMobile ? viewFadeIn : viewBlurIn;

  useEffect(() => {
    const t = setInterval(
      () => setCycleIndex((i) => (i + 1) % ROADMAP_NAMES.length),
      2000,
    );
    return () => clearInterval(t);
  }, []);

  return (
    <section
      id="sectors"
      className={`${MATTE} relative px-6 md:px-12 py-32 overflow-hidden`}
    >
      <StarField
        count={200}
        ring
        ringCount={260}
        ringRadiusFactor={0.37}
        ringBandWidth={50}
      />
      <LineField variant="projects" />
      <NoiseOverlay />

      <div className="relative z-[2] max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-12 mb-20">
        <m.h2
          className="font-display font-black text-5xl md:text-6xl uppercase leading-[0.95]"
          variants={headingVariants}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true, margin: "-100px" }}
        >
          MVP
          <br />
          Scope
        </m.h2>
        <div>
          <m.p
            className="text-white/55 text-[15px] max-w-md leading-relaxed"
            variants={headingVariants}
            initial="hidden"
            whileInView="show"
            viewport={{ once: true, margin: "-100px" }}
          >
            Pharmacy is the live, production-verified workflow. The other sectors
            are on the roadmap — the same human-in-the-loop pattern, not yet
            built.
          </m.p>
          <m.div
            className="mt-6 flex items-center gap-3 text-sm text-white/50"
            variants={headingVariants}
            initial="hidden"
            whileInView="show"
            viewport={{ once: true, margin: "-100px" }}
          >
            <span>Coming next:</span>
            <span className="inline-flex items-center rounded-full border border-amber/30 bg-amber/10 px-3 py-1 text-amber font-medium min-w-[140px] justify-center">
              {ROADMAP_NAMES[cycleIndex]}
            </span>
          </m.div>
        </div>
      </div>

      <div className="relative z-[2] max-w-7xl mx-auto grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 md:gap-8">
        {SECTORS.map((sector, i) => (
          <m.div
            key={sector.env}
            className="rounded-2xl p-6 border border-white/10 bg-[oklch(0.11_0.006_220)] hover:border-teal/40 hover:bg-[oklch(0.13_0.008_220)] transition-all duration-300 cursor-pointer group"
            variants={isMobile ? mobileCardIn : desktopCardIn(i * 0.1)}
            initial="hidden"
            whileInView="show"
            viewport={{ once: true, margin: "-80px" }}
          >
            <div className="w-12 h-12 rounded-xl bg-teal/10 flex items-center justify-center group-hover:bg-teal/20 transition">
              <sector.icon className="w-6 h-6 text-teal" />
            </div>
            <h3 className="font-display font-bold text-lg mt-4 text-white">
              {sector.name}
            </h3>
            <p className="text-white/55 text-sm mt-2 leading-relaxed">
              {sector.desc}
            </p>
            {sector.active && (
              <span className="mt-4 inline-flex items-center gap-1.5 rounded-full bg-green/20 border border-green/30 px-2 py-0.5 text-xs text-green">
                <span className="w-1.5 h-1.5 rounded-full bg-green" />
                Live MVP
              </span>
            )}
            {sector.roadmap && (
              <span className="mt-4 inline-flex items-center gap-1.5 rounded-full bg-amber/15 border border-amber/30 px-2 py-0.5 text-xs text-amber">
                Roadmap
              </span>
            )}
            <div className="mt-4">
              <span className="inline-flex rounded-full border border-teal/20 px-2 py-0.5 text-xs text-teal/60 font-mono bg-teal/5">
                {sector.env}
              </span>
            </div>
          </m.div>
        ))}
      </div>
    </section>
  );
}
