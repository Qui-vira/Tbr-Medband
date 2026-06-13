import { m } from "framer-motion";
import { ArrowUpRight } from "lucide-react";
import { LineField } from "../LineField";
import { StarField } from "../StarField";
import { NoiseOverlay } from "../shared/landing-ui";
import { LINKS, MATTE } from "@/lib/constants";
import {
  desktopCardIn,
  mobileCardIn,
  viewBlurIn,
  viewFadeIn,
  viewFadeUp,
} from "@/lib/motion";
import { FEATURED_INSTITUTIONS } from "@/lib/sectors";
import { useIsMobile } from "@/lib/useIsMobile";

export default function TrustedInstitutions() {
  const isMobile = useIsMobile();
  const headingVariants = isMobile ? viewFadeIn : viewBlurIn;

  return (
    <section
      id="institutions"
      className={`${MATTE} relative px-6 md:px-12 py-32 overflow-hidden`}
    >
      <StarField count={200} />
      <LineField variant="photographer" />
      <NoiseOverlay />
      <div
        className="absolute -right-20 top-1/3 w-[500px] h-[500px] rounded-full bg-teal/[0.03] blur-3xl pointer-events-none"
        style={{ zIndex: 1 }}
      />

      <div className="relative z-[2] max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-12 mb-20">
        <m.h2
          className="font-display font-black text-5xl md:text-6xl uppercase leading-[0.95]"
          variants={headingVariants}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true, margin: "-100px" }}
        >
          Institutions Already
          <br />
          On MedBand
        </m.h2>
        <m.p
          className="text-white/55 text-[15px] max-w-md leading-relaxed self-end"
          variants={headingVariants}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true, margin: "-100px" }}
        >
          Healthcare institutions across six sectors are already routing cases
          through MedBand. Join the network and connect your workflow to the
          multi-agent engine.
        </m.p>
      </div>

      <div className="relative z-[2] max-w-7xl mx-auto grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 md:gap-8">
        {FEATURED_INSTITUTIONS.map((inst, i) => (
          <m.div
            key={inst.id}
            className="rounded-2xl p-6 border border-white/10 bg-[oklch(0.11_0.006_220)] hover:border-teal/40 hover:bg-[oklch(0.13_0.008_220)] transition-all duration-300"
            variants={isMobile ? mobileCardIn : desktopCardIn(i * 0.08)}
            initial="hidden"
            whileInView="show"
            viewport={{ once: true, margin: "-80px" }}
          >
            <div className="flex items-start gap-4">
              <div
                className="w-12 h-12 rounded-full flex items-center justify-center font-display font-bold text-lg text-white shrink-0"
                style={{ backgroundColor: inst.logo_color }}
              >
                {inst.logo_initial}
              </div>
              <div className="min-w-0 flex-1">
                <h3 className="font-display font-bold text-lg text-white truncate">
                  {inst.name}
                </h3>
                <p className="text-white/50 text-sm mt-0.5">{inst.location}</p>
              </div>
            </div>

            <span className="mt-4 inline-flex rounded-full border border-teal/20 px-2 py-0.5 text-xs text-teal/80 bg-teal/5">
              {inst.sector}
            </span>

            <div className="mt-4 grid grid-cols-3 gap-2 text-center">
              <div className="rounded-lg bg-white/[0.03] px-2 py-2">
                <div className="font-display font-bold text-teal text-sm">
                  {inst.rating}
                </div>
                <div className="text-white/40 text-[10px] mt-0.5">Rating</div>
              </div>
              <div className="rounded-lg bg-white/[0.03] px-2 py-2">
                <div className="font-display font-bold text-teal text-sm">
                  {inst.cases_processed.toLocaleString()}
                </div>
                <div className="text-white/40 text-[10px] mt-0.5">Cases</div>
              </div>
              <div className="rounded-lg bg-white/[0.03] px-2 py-2">
                <div className="font-display font-bold text-teal text-xs leading-tight">
                  {inst.turnaround}
                </div>
                <div className="text-white/40 text-[10px] mt-0.5">
                  Turnaround
                </div>
              </div>
            </div>

            <span
              className={`mt-4 inline-flex rounded-full px-2 py-0.5 text-xs capitalize ${
                inst.plan === "enterprise"
                  ? "bg-teal/20 border border-teal/30 text-teal"
                  : "bg-white/10 border border-white/20 text-white/70"
              }`}
            >
              {inst.plan}
            </span>
          </m.div>
        ))}
      </div>

      <m.div
        className="relative z-[2] max-w-7xl mx-auto mt-16 text-center"
        variants={isMobile ? viewFadeIn : viewFadeUp}
        initial="hidden"
        whileInView="show"
        viewport={{ once: true, margin: "-100px" }}
      >
        <a
          href={LINKS.register}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 rounded-full bg-teal text-white px-8 py-3 font-medium hover:bg-teal/80 transition"
        >
          Register Your Institution
          <ArrowUpRight className="w-4 h-4" />
        </a>
      </m.div>
    </section>
  );
}
