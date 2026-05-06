import logoImg from "@/assets/logo_app.png"
import { TextEffect } from "../motion-primitives/text-effect"

type GymTrackerLogoProps = {
    trigger?: boolean;
}

export const GymTrackerLogo = ({ trigger = false }: GymTrackerLogoProps) => {
    return (
        <div className="flex flex-row items-center gap-3">
            <img src={logoImg} alt="Gym Tracker" className="w-14 h-auto" />
            <div className="w-px h-14 bg-violet-400" />
            <div className="flex flex-col">
                <span className="text-white font-bold text-[23px] tracking-widest leading-none">
                    {trigger ? (
                        <TextEffect per="word" preset="slide" trigger={trigger}>GYM</TextEffect>
                    ) : (
                        <span>GYM</span>
                    )}
                </span>
                <span className="text-white font-normal text-[13px] tracking-[0.3em] leading-tight">
                    {trigger ? (
                        <TextEffect per="word" preset="slide" delay={0.2} trigger={trigger}>TRACKER</TextEffect>
                    ) : (
                        <span>TRACKER</span>
                    )}
                </span>
            </div>
        </div>
    )
}