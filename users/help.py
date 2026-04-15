class GetAllRutines(request):
    """
     Aca le pedis que te traiga todas las rutinas.
     Se fija que rol tenes
     SI pasas el query Parameter gym (EL ID), filtra por ese gym
     
    """    
    serializer_class = RoutineSerializer 
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        
        user = self.request.user
        gym_id = self.request.query_params.get('gym')
        
        #si person
        if user.role == 'PERSON':
            qs = Routine.objects.filter(person=user)
            if gym_id :
                qs = qs.filter(gym_id=gym_id)
            return qs

        #Si staff
        elif user.role == 'STAFF':
            qs = Routine.objects.filter(staff=user)
            if gym_id :
                qs = qs.filter(gym_id=gym_id)
            return  qs

        #Si admin
        elif user.role == 'ADMIN':

            qs = Routine.objects.filter(gym__in=user.gyms.all())
            
            if gym_id:
               
                qs = qs.filter(gym_id=gym_id)
            return qs

        
        # devulve nada por las dudas
        return Routine.objects.none()
    
