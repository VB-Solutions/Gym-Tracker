import { GymTrackerLogo } from "@/components/ui/svg-logo"
import { Link, useLocation } from "react-router-dom"
import { TextEffect } from "./motion-primitives/text-effect"
import { useEffect, useState } from "react";

/*
    TODO
    - Animar los links cuando hoveas
    - Hacer que el ancho, cuando se achique a cierto punto, pase a full
    - Que no te deje ir al home cuando no iniciaste sesión y clickees en el logo
    - Mas adelante: cambiar estado de links (chequeos)
*/
export const Navbar = () => {
    const { pathname } = useLocation();
    const isHome = pathname === '/' || pathname === '/home';
    const [trigger, setTrigger] = useState(isHome);
    const [animated, setAnimated] = useState(false);

    useEffect(() => {
        if (isHome && !animated) {
        setTrigger(true);
        } else {
        setTrigger(false);
        setAnimated(false);
        }
    }, [pathname]);

    return (
        <div className="bg-violet-300 w-full h-[10vh] sticky top-0 z-50 flex justify-center border-y border-y-gray-500">
            <div className="w-[65%] flex flex-row items-center">
                <Link to="/home" className="cursor-pointer">
                    <GymTrackerLogo trigger={trigger}/>
                </Link>
                <div className="flex-1"/>
                <Link to="/login" className="pe-2 text-violet-500 hover:text-violet-100 cursor-pointer font-bold">
                    {isHome ? (
                        <TextEffect per="char" as="h2" preset="fade" trigger={trigger} onAnimationComplete={() => setAnimated(true)}>
                            Iniciar sesión
                        </TextEffect>
                    ) : (
                        <h2>Iniciar sesión</h2>
                    )}
                </Link>
                <div className="w-px h-4 bg-violet-400" />
                <Link to="/register" className="ps-2 text-violet-500 hover:text-violet-100 cursor-pointer font-bold">
                    {isHome ? (
                        <TextEffect per="char" as="h2" preset="fade" trigger={trigger} onAnimationComplete={() => setAnimated(true)}>
                            Crear cuenta
                        </TextEffect>
                    ) : (
                        <h2>Crear cuenta</h2>
                    )}
                </Link>
            </div>
        </div>
    )
}