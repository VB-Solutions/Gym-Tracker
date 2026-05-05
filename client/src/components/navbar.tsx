import { GymTrackerLogo } from "@/components/ui/svg-logo"
import { Link } from "react-router-dom"

/*
    TODO
    - Animar los links cuando hoveas
    - Hacer que el ancho, cuando se achique a cierto punto, pase a full
    - Que no te deje ir al home cuando no iniciaste sesión y clickees en el logo
    - Mas adelante: cambiar estado de links (chequeos)
*/
export const Navbar = () => {
    return (
        <div className="bg-violet-300 w-full h-[10vh] sticky top-0 z-50 flex justify-center border-y border-y-gray-500">
            <div className="w-[65%] flex flex-row items-center">
                <Link to="/home" className="cursor-pointer"><GymTrackerLogo /></Link>
                <div className="flex-1"/>
                <Link to="/login" className="pe-2 text-violet-600 hover:text-white cursor-pointer font-bold">Iniciar sesi&oacute;n</Link>
                <div className="w-px h-4 bg-violet-500" />
                <Link to="/register" className="ps-2 text-violet-600 hover:text-white cursor-pointer font-bold">Registrarme</Link>
            </div>
        </div>
    )
}