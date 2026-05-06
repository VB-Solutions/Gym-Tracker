import { Footer } from "@/components/footer.tsx"
import { Navbar } from "@/components/navbar.tsx"
import { Item, ItemHeader, ItemTitle, ItemContent, ItemDescription, ItemGroup} from "@/components/ui/item.tsx"
import { Magnetic } from "@/components/motion-primitives/magnetic";

/*
   TODO
   - Hacer que el item sea clickeable cuando hoveas y que te lleve a una view
   - Capaz poner fondo (animado en lo posible)
   - Mas adelante: 
      - handleSelection
      - Cargar los items desde la db
*/
export const Home = () => {

   //const handleSelection = async () =>{}

   return (
    <div className="flex flex-col items-center content-center min-h-screen">
      <Navbar/>

      <div className="w-[70%] flex-1 justify-center items-center content-center flex flex-col">
         <ItemGroup className="bg-scroll p-7 justify-center items-center content-center grid grid-cols-2 md:grid-cols-4 gap-4 overflow-y-auto">

            <Magnetic>
               <Item className="animate-in fade-in slide-in-from-bottom-4 duration-500 w-full border border-gray-300 cursor-pointer shadow-black-bl hover:shadow-black-bl transition-shadow duration-500">
                  <ItemHeader className="flex flex-col items-center">
                     <ItemTitle className="text-yellow-500">Servicio 1</ItemTitle>
                  </ItemHeader>
                  <ItemContent className="flex flex-col items-center justify-center size-32">
                     <ItemDescription>Descripcion breve</ItemDescription>
                  </ItemContent>
               </Item>
            </Magnetic>

            <Magnetic>
               <Item className="w-full border border-gray-300 animate-in fade-in slide-in-from-bottom-4 duration-500 cursor-pointer shadow-black-bl hover:shadow-black-bl transition-shadow duration-500">
                  <ItemHeader className="flex flex-col items-center">
                     <ItemTitle className="text-yellow-500">Servicio 2</ItemTitle>
                  </ItemHeader>
                  <ItemContent className="flex flex-col items-center justify-center size-32">
                     <ItemDescription>Descripcion breve</ItemDescription>
                  </ItemContent>
               </Item>
            </Magnetic>

            <Magnetic>
               <Item className="w-full border border-gray-300 animate-in fade-in slide-in-from-bottom-4 duration-500 cursor-pointer shadow-black-bl hover:shadow-black-bl transition-shadow duration-500">
                  <ItemHeader className="flex flex-col items-center">
                     <ItemTitle className="text-yellow-500">Servicio 3</ItemTitle>
                  </ItemHeader>
                  <ItemContent className="flex flex-col items-center justify-center size-32">
                     <ItemDescription>Descripcion breve</ItemDescription>
                  </ItemContent>
               </Item>
            </Magnetic>  

            <Magnetic>
               <Item className="w-full border border-gray-300 animate-in fade-in slide-in-from-bottom-4 duration-500 cursor-pointer shadow-black-bl hover:shadow-black-bl transition-shadow duration-500">
                  <ItemHeader className="flex flex-col items-center">
                     <ItemTitle className="text-yellow-500">Servicio 4</ItemTitle>
                  </ItemHeader>
                  <ItemContent className="flex flex-col items-center justify-center size-32">
                     <ItemDescription>Descripcion breve</ItemDescription>
                  </ItemContent>
               </Item>
            </Magnetic>

            <Magnetic>
               <Item className="w-full border border-gray-300 animate-in fade-in slide-in-from-bottom-4 duration-500 cursor-pointer shadow-black-bl hover:shadow-black-bl transition-shadow duration-500">
                  <ItemHeader className="flex flex-col items-center">
                     <ItemTitle className="text-yellow-500">Servicio 5</ItemTitle>
                  </ItemHeader>
                  <ItemContent className="flex flex-col items-center justify-center size-32">
                     <ItemDescription>Descripcion breve</ItemDescription>
                  </ItemContent>
               </Item>
            </Magnetic>

         </ItemGroup>
      </div>
      
      <Footer/>
    </div>
   ) 
}