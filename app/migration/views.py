from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework import status

from app.migration.serializer import CalculationTypesSerializer
from app.migration.serializer import ApplicationSerializer
from app.migration.serializer import ApplicationDetailedSerializer
from app.migration.models import CalculationTypes
from app.migration.models import ApplicationForCalculation
from app.migration.models import ApplicationsCalculations
from app.migration.models import Users

from minio import Minio
import os
from rest_framework.decorators import api_view
from datetime import datetime

from app.migration.s3 import delete_image_from_s3, upload_image_to_s3, get_image_from_s3

client = Minio(endpoint="localhost:9000",   # адрес сервера
               access_key='minio',          # логин админа
               secret_key='minio124',       # пароль админа
               secure=False)

@api_view(['Get'])
def get_calculations_list(request, format=None):
    """
    Возвращает список операций
    """
    try:
        inserted_application = get_object_or_404(ApplicationForCalculation,application_status="Inserted")
        print(f'!!!{inserted_application.application_id}!!!')
    except:
        inserted_application = None
        pass
    print(inserted_application)


    print('get')
    query = request.GET.get("title")
    print(query)
    if query:
        calculation_types = CalculationTypes.objects.filter(calculation_name__icontains=query, calculation_status="Active")
    else:
        calculation_types = CalculationTypes.objects.filter(calculation_status="Active")
    serializer = CalculationTypesSerializer(calculation_types, many=True)
    #print(serializer)
    print(type(serializer.data))
    if inserted_application:
        my_dict = [f'inserted application id = {inserted_application.application_id}', serializer.data]
        return Response(my_dict, template_name='tort')
    return Response(serializer.data, template_name='tort')

@api_view(['Get'])
def get_calculations_detailed(request, pk, format=None):
    """
    Возвращает данные конкретной операции
    """
    calculation_type = get_object_or_404(CalculationTypes, pk=pk)
    if request.method == 'GET':
        serializer = CalculationTypesSerializer(calculation_type)
        return Response(serializer.data)


@api_view(["Post"])
def create_calculation_type_s(request, format=None):
    serializer = CalculationTypesSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(["Post"])
def create_calculation_type(request, format=None):
    serializer = CalculationTypesSerializer(data=request.data)
    if serializer.is_valid():
        if not 'image' in request.data:
            serializer.validated_data['calculation_image_url'] = 'base.png'
            serializer.save()
        else:
            try:

                if 'image' in request.data:
                    #client.remove_object("pictures", f"{calculation_types.calculation_image_url}")
                    print('here')
                    print(str(request.data['image']))
                    
                    client.fput_object(bucket_name='pictures',  
                                    object_name=str(request.data['image']),
                                    file_path= f"app/static/images/{request.data['image']}")
                    print('there 0')
                    serializer.validated_data['calculation_image_url'] = str(request.data['image'])
                    print('there')
                    serializer.save()

            except:
                serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(["POST"])
def add_calculation_type(request, pk, format=None):
    calculation_id = pk
    inserted_application = ApplicationForCalculation.objects.filter(application_status='Inserted').first()
    if inserted_application:
        print("inserted_application")

        inserted_application.save()
        print(f"calculation_id = {calculation_id}")
        if calculation_id:
            try:
                calculation_type = CalculationTypes.objects.get(calculation_id=calculation_id)
            except CalculationTypes.DoesNotExist:
                return Response({'error': 'Calculation not found'}, status=status.HTTP_404_NOT_FOUND)

            calculation_status = calculation_type.calculation_status
            print(calculation_status)
            if calculation_status != "Active":
                return Response({'error': 'Calculation not found'}, status=status.HTTP_404_NOT_FOUND)
            ApplicationsCalculations.objects.create(calculation=calculation_type, application=inserted_application)

        return Response({'message': 'Calculation type added to the existing inserted application'}, status=status.HTTP_200_OK)
    else:
        current_user = Users.objects.get(user_id=1) #????????
        new_application = ApplicationForCalculation.objects.create(
            user=current_user,
            application_status='Inserted'
        )

        calculation_id = request.data.get('calculation_id')
        print(f"calculation_id = {calculation_id}")
        if calculation_id:
            try:
                calculation_type = CalculationTypes.objects.get(calculation_id=calculation_id)
                ApplicationsCalculations.objects.create(calculation_id=calculation_type, application_id=new_application)
            except CalculationTypes.DoesNotExist:
                new_application.delete()  
                return Response({'error': 'Calculation type not found'}, status=status.HTTP_404_NOT_FOUND)

        return Response({'message': 'New service application created with the calculation type'}, status=status.HTTP_201_CREATED)
    

@api_view(["PUT"])
def change_calculation_type_data(request, pk, format=None):
    calculation_type = get_object_or_404(CalculationTypes, pk=pk)
    serializer = CalculationTypesSerializer(calculation_type, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(["PUT"])
def change_calculation_image(request, pk, format=None):
    print('aaaaaa')
    calculation_type = get_object_or_404(CalculationTypes, pk=pk)
    print('aaaaaa1')
    object_list = client.list_objects(bucket_name='pictures')
    for obj in object_list:
        print('имя файла: ', obj.object_name, 
          'размер: ', obj.size, 
          'дата последнего изменения: ', obj.last_modified) # и т.д.

    serializer = CalculationTypesSerializer(calculation_type, data=request.data, partial=True)
    print(os.listdir(path='app/static/images'))


    if serializer.is_valid():
        try:
            print(request.data['image'])
            print(calculation_type.calculation_image_url)
            if calculation_type.calculation_image_url != request.data['image']:
                #client.remove_object("pictures", f"{calculation_types.calculation_image_url}")
                print('here')
                print(str(request.data['image']))
                
                client.fput_object(bucket_name='pictures',  
                                   object_name=str(request.data['image']),
                                   file_path= f"app/static/images/{request.data['image']}")
                print('there 0')
                serializer.validated_data['full_url'] = str(request.data['image'])
                serializer.validated_data['calculation_image_url'] = str(request.data['image'])
                print('there')
                serializer.save()
        except:
            serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(["Delete"])
def delete_calculation(request, pk, format=None):
    calculation_type = get_object_or_404(CalculationTypes, pk=pk)
    calculation_type.calculation_status = "Deleted"
    calculation_type.save()
    return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(["Get"])
def get_applications_list(request, format=None):
    print(request.data)
    '''start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    status = request.GET.get('status')'''
    data = request.data
    if data['start_date']:
        start_date = data['start_date']
    else:
        start_date = None
    if 'end_date' in data:
        end_date = data['end_date']
    else:
        end_date = None
    if data['status']:
        status = data['status']
    else:
        status = None
    print(start_date)
    print(status)
    applications_list = ApplicationForCalculation.objects.all()

    if start_date:
        applications_list = applications_list.filter(date_application_create__gte=start_date)
        if end_date:
            applications_list = applications_list.filter(date_application_create__lte=end_date)
    if status:
        print("aaaa")
        applications_list = applications_list.filter(application_status=status)

    applications_list = applications_list.order_by('-date_application_create')
    serializer = ApplicationSerializer(applications_list, many=True)
    return Response(serializer.data)

@api_view(["Get"])
def get_application_detailed(request, pk, format=None):
    application = get_object_or_404(ApplicationForCalculation, pk=pk)
    serializer = ApplicationDetailedSerializer(application)

    return Response(serializer.data)

@api_view(['PUT'])
def change_inputs_application(request, pk, format=None):
    """
    Обновляет информацию в заявке - surname and reason
    """
    application = get_object_or_404(ApplicationForCalculation, pk=pk)
    if application.application_status != 'Inserted':
        return Response({"error": "Неверный статус."}, status=400)
    if request.data['input_first_param'] and request.data['input_first_param'] != application.input_first_param:
        application.input_first_param = request.data['input_first_param']
    if request.data['input_second_param'] and request.data['input_second_param'] != application.input_second_param:
        application.input_second_param = request.data['input_second_param']
    serializer = ApplicationDetailedSerializer(application, data=request.data, partial=True) #AplSer
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(["DELETE"])
def delete_calculation_from_application(request, application_id,
                                        calculation_id, format=None):
    application = get_object_or_404(ApplicationForCalculation, pk=application_id)

    applications_calculations = get_object_or_404(ApplicationsCalculations, application_id=application, calculation_id=calculation_id)

    applications_calculations.delete()

    serializer = ApplicationDetailedSerializer(application) #AplSer
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(["DELETE"])
def delete_application_for_calculation(request, application_id, format=None):
    application = get_object_or_404(ApplicationForCalculation,
                                    pk=application_id)
    if application.application_status != 'Inserted':
        return Response({"error": "Неверный статус."}, status=400)
    user_id = request.query_params.get('user_id')
    print(user_id)

    try:
        user = Users.objects.get(user_id=user_id)
        if user.role != 'Moderator':
            return Response({'error': 'User does not have Moderator status'}, status=status.HTTP_403_FORBIDDEN)
    except Users.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    application.application_status = 'Deleted'
    application.save()

    return Response({'message': 'Application deleted successfully'}, status=status.HTTP_204_NO_CONTENT)

@api_view(['PUT']) 
def put_applications_moderator(request, pk, format=None):
    """
    Обновляет информацию о заявке модератором
    """
    application = get_object_or_404(ApplicationForCalculation, pk=pk)
    print(application.application_status)
    print(f'_______{request.data}__________')
    if request.data['application_status'] not in ['Finished', 'Canceled'] or application.application_status == 'Inserted':
        return Response({"error": "Неверный статус."}, status=400)
    application.application_status = request.data['application_status']
    application.date_application_complete = datetime.now()
    serializer = ApplicationSerializer(application, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['PUT']) 
def put_applications_client(request, pk, format=None):
    """
    Обновляет информацию о заявке клиентом
    """
    application = get_object_or_404(ApplicationForCalculation, pk=pk)
    print(f'_______{request.data}__________')
    if request.data['application_status'] != 'In service' or application.application_status != 'Inserted':
        return Response({"error": "Неверный статус."}, status=400)
    application.application_status = request.data['application_status']
    application.date_application_accept = datetime.now()
    serializer = ApplicationSerializer(application, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
def edit_result_applications_calculations(request, pk, calculation_id, format=None):
    try:
        new_result = request.data.get('new_result')
        print('a')
        application_calculation = ApplicationsCalculations.objects.filter(application_id=pk, calculation_id=calculation_id).first()
        print('b')
        if application_calculation:
            application_calculation.result = new_result
            application_calculation.save()
            print('c')
            return Response("Успешно", status=status.HTTP_200_OK)
        else:
            print('d')
            return Response("Не найдено", status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        print('e')
        return Response(str(e), status=status.HTTP_400_BAD_REQUEST)