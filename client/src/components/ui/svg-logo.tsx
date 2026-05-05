import logoImg from "@/assets/logo_app.png"

export const GymTrackerLogo = () => {
    return (
        <div className="flex flex-row items-center gap-3">
            <img src={logoImg} alt="Gym Tracker" className="w-14 h-auto" />
            <div className="w-px h-14 bg-violet-500" />
            <div className="flex flex-col">
                <span className="text-white font-bold text-[23px] tracking-widest leading-none">
                    GYM
                </span>
                <span className="text-white font-normal text-[13px] tracking-[0.3em] leading-tight">
                    TRACKER
                </span>
            </div>
        </div>
    )
}