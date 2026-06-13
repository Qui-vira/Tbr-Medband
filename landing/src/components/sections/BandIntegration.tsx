import { useRef } from "react";
import { m, useScroll, useTransform } from "framer-motion";
import { MoveRight, Shield, Users, Zap } from "lucide-react";
import { LineField } from "../LineField";
import { StarField } from "../StarField";
import { SafeImage, NoiseOverlay } from "../shared/landing-ui";
import { ASSETS, EASE, LINKS } from "@/lib/constants";
import { viewFadeIn, viewFadeUp } from "@/lib/motion";
import { useIsMobile } from "@/lib/useIsMobile";

export default function BandIntegration() {
  const isMobile = useIsMobile();
  const bottomRef = useRef<HTMLDivElement>(null);

  const { scrollYProgress } = useScroll({
    target: bottomRef,
    offset: ["start end", "end start"],
  });

  const parallaxY = useTransform(scrollYProgress, [0, 1], ["0%", "-15%"]);

  const headingInitial = isMobile
    ? { opacity: 0 }
    : { opacity: 0, y: 40, filter: "blur(16px)" };
  const headingAnimate = isMobile
    ? { opacity: 1 }
    : { opacity: 1, y: 0, filter: "blur(0px)" };

  return (
    <section id="band-integration">
      <div className="relative px-6 md:px-12 pt-28 pb-12 overflow-hidden">
        <StarField count={200} />
        <LineField variant="marvels" />
        <NoiseOverlay />

        <m.h2
          className="relative z-10 font-display font-medium uppercase text-4xl sm:text-5xl md:text-6xl lg:text-7xl xl:text-[80px] leading-[0.95] max-w-[1100px] break-words"
          initial={headingInitial}
          whileInView={headingAnimate}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: isMobile ? 0.6 : 1.2, ease: EASE }}
        >
          Powered by{" "}
          <SafeImage
            src={ASSETS.bandRoom}
            alt=""
            decorative
            className="inline-block h-10 md:h-16 w-auto rounded-md align-middle mx-1"
          />{" "}
          Band: Every agent. Every message. Every decision.
        </m.h2>

        <div className="relative z-10 flex gap-4 flex-wrap mt-8">
          {[
            { icon: Zap, label: "Real-time WebSocket" },
            { icon: Shield, label: "Full Audit Trail" },
            { icon: Users, label: "4 Active Agents" },
          ].map(({ icon: Icon, label }) => (
            <span
              key={label}
              className="rounded-full border border-white/20 px-4 py-2 text-sm text-white/70 flex items-center gap-2"
            >
              <Icon className="w-3.5 h-3.5 text-teal" />
              {label}
            </span>
          ))}
        </div>

        <div className="relative z-10 flex justify-between items-center mt-16 text-xs uppercase tracking-widest text-white/50">
          <a
            href={LINKS.github}
            target="_blank"
            rel="noopener noreferrer"
            className="group flex items-center gap-2 hover:text-white transition"
          >
            View on GitHub
            <MoveRight className="w-3.5 h-3.5 -rotate-45 group-hover:translate-x-1 transition" />
          </a>
          <a
            href={LINKS.live}
            target="_blank"
            rel="noopener noreferrer"
            className="group flex items-center gap-2 hover:text-white transition"
          >
            Submit a Case
            <MoveRight className="w-3.5 h-3.5 -rotate-45 group-hover:translate-x-1 transition" />
          </a>
        </div>
      </div>

      <div ref={bottomRef} className="relative h-[80vh] overflow-hidden">
        <m.div
          className="absolute -top-[10%] -bottom-[10%] inset-x-0"
          style={{
            y: isMobile ? undefined : parallaxY,
            background:
              "linear-gradient(135deg, oklch(0.08 0.04 220) 0%, oklch(0.04 0.02 240) 50%, oklch(0.06 0.06 180) 100%)",
          }}
        />
        {[
          { top: "20%", left: "15%", size: 300 },
          { top: "60%", left: "70%", size: 400 },
          { bottom: "10%", left: "40%", size: 250 },
        ].map((orb, i) => (
          <div
            key={i}
            className="absolute rounded-full bg-teal opacity-15 blur-3xl pointer-events-none"
            style={{
              width: orb.size,
              height: orb.size,
              top: orb.top,
              left: orb.left,
              bottom: orb.bottom,
            }}
            aria-hidden
          />
        ))}
        <div className="absolute inset-0 bg-gradient-to-t from-black/30 via-transparent to-black/20 pointer-events-none" />
        <LineField variant="marvelsBottom" />

        <div className="relative z-10 h-full grid place-items-center px-6 text-center">
          <div>
            <m.h3
              className="font-display font-black uppercase text-4xl md:text-6xl leading-none tracking-tight"
              initial={headingInitial}
              whileInView={headingAnimate}
              viewport={{ once: true, margin: "-100px" }}
              transition={{ duration: isMobile ? 0.6 : 1.2, ease: EASE }}
            >
              Build a band,
              <br />
              <span className="text-teal">not a soloist.</span>
            </m.h3>
            <m.p
              className="mt-6 text-white/55 text-lg max-w-lg mx-auto"
              variants={isMobile ? viewFadeIn : viewFadeUp}
              initial="hidden"
              whileInView="show"
              custom={0.2}
              viewport={{ once: true, margin: "-100px" }}
            >
              3+ agents collaborating through Band — planning, execution,
              review, decisions, handoffs.
            </m.p>
            <m.div
              className="mt-10 flex items-center justify-center gap-4 flex-wrap"
              variants={isMobile ? viewFadeIn : viewFadeUp}
              initial="hidden"
              whileInView="show"
              custom={0.3}
              viewport={{ once: true, margin: "-100px" }}
            >
              <a
                href={LINKS.live}
                target="_blank"
                rel="noopener noreferrer"
                className="rounded-full bg-teal text-white px-8 py-3 font-medium hover:bg-teal/80 transition"
              >
                Submit a Case
              </a>
              <a
                href={LINKS.github}
                target="_blank"
                rel="noopener noreferrer"
                className="rounded-full border border-white/20 text-white/70 px-8 py-3 hover:bg-white/5 transition"
              >
                View GitHub
              </a>
            </m.div>
          </div>
        </div>
      </div>
    </section>
  );
}
