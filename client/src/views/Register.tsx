import { Footer } from "@/components/footer.tsx"
import { Navbar } from "@/components/navbar.tsx"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

/*
   TODO
   - Implementar el handler
*/
export const Register = () => {

   const handleRegister = async () =>{}
   

   return (
      <div className="flex flex-col items-center content-center min-h-screen">
         <Navbar/>

         <div className="w-[70%] flex-1 justify-center items-center content-center flex flex-col">
            <Card className="w-full max-w-lg flex flex-col">

               <CardHeader className="flex flex-col items-center justify-center">
                  <CardTitle className="flex flex-col items-center justify-center text-yellow-500 text-[21px] font-bold">Crear una cuenta</CardTitle>
               </CardHeader>

               <CardContent>
                  <form>
                     <div className="flex flex-col gap-6">

                        <div className="grid gap-2">
                           <Label htmlFor="email">Correo</Label>
                           <Input placeholder="correo@ejemplo.com" required/>
                        </div>

                        <div className="grid gap-2">
                           <Label htmlFor="password">Contraseña</Label>
                           <Input type="password" required />
                        </div>

                        <div className="grid gap-2">
                           <Label htmlFor="password">Confirmar contraseña</Label>
                           <Input id="password" type="password" required />
                        </div>

                     </div>
                  </form>
               </CardContent>

               <CardFooter className="flex flex-col">
                  <Button onClick={handleRegister} className="hover:bg-gray-400 bg-yellow-500 cursor-pointer ">Continuar</Button>
               </CardFooter>

            </Card>
         </div>
         
         <Footer/>
      </div>
   ) 
}