from django.shortcuts import get_object_or_404, render
from rest_framework.views import APIView, Request, Response, status
from .models import Pet
from groups.models import Group
from traits.models import Trait
from .serializers import PetSerializer
from rest_framework.pagination import PageNumberPagination



class PetView(APIView, PageNumberPagination):
      def get(self, req: Request) -> Response:
        pet_traits = req.query_params.get("trait", None)
        if pet_traits:
            pet = Pet.objects.filter(traits__name = pet_traits)
        else:
            pet = Pet.objects.all()

        paginated_result = self.paginate_queryset(pet, req, view = self)
        serializer = PetSerializer(paginated_result, many = True)
        return self.get_paginated_response(serializer.data)

      
      def post(self, req: Request) -> Response:
          serializer = PetSerializer(data = req.data)
          serializer.is_valid(raise_exception = True)
          group_data = serializer.validated_data.pop("group")
          group_name = group_data["scientific_name"]
          traits_data = serializer.validated_data.pop("traits")
          try:
             group = Group.objects.get(scientific_name = group_name)
          except Group.DoesNotExist:
             group = Group.objects.create(**group_data)

          pet = Pet.objects.create(**serializer.validated_data, group = group)

          traits = []
          for trait_data in traits_data:
            trait_name = trait_data["name"].lower()
            try:
                trait = Trait.objects.get(name__iexact=trait_name)
            except Trait.DoesNotExist:
                trait = Trait.objects.create(name=trait_name)
            traits.append(trait)
          pet.traits.set(traits)
            
          serializer = PetSerializer(instance = pet)
          return Response(serializer.data, status = status.HTTP_201_CREATED)


class DetailedPetView(APIView):
       def get(self, req: Request, pet_id: int) -> Response:
         pet = get_object_or_404(Pet,id = pet_id)
         serializer = PetSerializer(pet)
         return Response(serializer.data, status = status.HTTP_200_OK)
       
       def delete(self, req: Request, pet_id: int) -> Response:
        pet = get_object_or_404(Pet,id=pet_id)
        pet.delete()
        return Response(status = status.HTTP_204_NO_CONTENT)
       
       def patch(self, req: Request, pet_id: int) -> Response:
        pet = get_object_or_404(Pet, id = pet_id)
        serializer = PetSerializer(data = req.data, partial = True)
        serializer.is_valid(raise_exception = True)

        if "group" in req.data:
            group_data = serializer.validated_data.pop("group")
            try:
                group = Group.objects.get(scientific_name = group_data["scientific_name"])
            except Group.DoesNotExist:
                group = Group.objects.create(**group_data)
            setattr(pet, "group", group)
        else:
            setattr(pet, "group", pet.group)

            traits_data = serializer.validated_data.pop("traits")
            if "traits" in req.data:
                traits = []
            for trait_data in traits_data:
                try:
                    trait = Trait.objects.get(name__iexact=trait_data["name"])
                    traits.append(trait)
                except Trait.DoesNotExist:
                    trait = Trait.objects.create(**trait_data)
                    traits.append(trait)
            pet.traits.set(traits)
        for key, value in serializer.validated_data.items():
            setattr(pet, key, value)
        pet.save()
        serializer = PetSerializer(pet)
        return Response(serializer.data, status = status.HTTP_200_OK)
    