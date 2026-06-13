import { LogoMark } from "../LogoMark";
import { LINKS } from "@/lib/constants";
import { SECTORS } from "@/lib/sectors";

export default function Footer() {
  return (
    <footer className="relative border-t border-white/10 px-6 md:px-12 py-12">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <LogoMark style={{ fontSize: "1.25rem", lineHeight: 1.2 }} />
        <div className="flex gap-6">
          {[
            { label: "GitHub", href: LINKS.github },
            { label: "Live Demo", href: LINKS.live },
            { label: "Register Institution", href: LINKS.register },
            { label: "Pricing", href: `${LINKS.register}#pricing` },
            { label: "Hackathon", href: LINKS.github },
          ].map((link) => (
            <a
              key={link.label}
              href={link.href}
              target="_blank"
              rel="noopener noreferrer"
              className="text-white/40 hover:text-white text-sm transition"
            >
              {link.label}
            </a>
          ))}
        </div>
      </div>

      <div className="mt-8 pt-8 border-t border-white/10 grid grid-cols-1 md:grid-cols-3 gap-8">
        <div>
          <p className="font-display font-bold mb-2">
            <LogoMark style={{ fontSize: "1rem", lineHeight: 1.2 }} />
          </p>
          <p className="text-white/40 text-sm leading-relaxed">
            A sector-configurable multi-agent healthcare workflow engine. Built
            for Band of Agents Hackathon 2026.
          </p>
        </div>
        <div>
          <p className="font-medium text-white text-sm mb-3">Sectors</p>
          <ul className="space-y-2">
            {SECTORS.map((s) => (
              <li key={s.env}>
                <span className="text-white/40 text-sm hover:text-white transition cursor-default">
                  {s.name}
                </span>
              </li>
            ))}
          </ul>
        </div>
        <div>
          <p className="font-medium text-white text-sm mb-3">Built by</p>
          <p className="text-white/60 text-sm">
            The Billionaire Republic (TBR)
          </p>
          <p className="text-white/40 text-sm mt-2 leading-relaxed">
            Turning ideas into real products, businesses, and income-generating
            opportunities.
          </p>
        </div>
      </div>

      <div className="mt-8 pt-6 border-t border-white/10 flex items-center justify-between flex-wrap gap-4">
        <p className="text-white/30 text-xs">
          © 2026 MedBand by The Billionaire Republic. All rights reserved.
        </p>
        <p className="text-white/30 text-xs">
          Band of Agents Hackathon 2026 · Track 3: Regulated Workflows
        </p>
      </div>
    </footer>
  );
}
