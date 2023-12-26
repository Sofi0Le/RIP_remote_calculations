from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework import status as drf_status

from app.migration.serializer import CalculationTypesSerializer
from app.migration.serializer import ApplicationSerializer
from app.migration.serializer import ApplicationDetailedSerializer
from app.migration.serializer import ApplicationsCalculationsSerializer
from app.migration.models import CalculationTypes
from app.migration.models import ApplicationForCalculation
from app.migration.models import ApplicationsCalculations
from app.migration.models import Users

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from django.utils import timezone
import requests

from rest_framework.decorators import parser_classes
from rest_framework.parsers import JSONParser

from django.db.models import Q

from minio import Minio
import os
from rest_framework.decorators import api_view
from datetime import datetime
from datetime import date

import hashlib
import secrets
from django.http import JsonResponse
import json

from app.migration.redis_view import (
    set_key,
    get_value,
    delete_value
)

def check_user(request):
    response = login_view_get(request._request)
    if response.status_code == 200:
        user = Users.objects.get(user_id=response.data.get('user_id').decode())
        return user.role == 'User'
    return False

def check_authorize(request):
    response = login_view_get(request._request)
    if response.status_code == 200:
        user = Users.objects.get(user_id=response.data.get('user_id'))
        return user
    return None

def check_moderator(request):
    response = login_view_get(request._request)
    if response.status_code == 200:
        user = Users.objects.get(user_id=response.data.get('user_id'))
        return user.role == 'Moderator'
    return False

client = Minio(endpoint="localhost:9000",   # адрес сервера
               access_key='minio',          # логин админа
               secret_key='minio124',       # пароль админа
               secure=False)


@api_view(['POST'])
def registration(request, format=None):
    required_fields = ['first_name', 'last_name', 'email', 'login', 'password', 'role']
    missing_fields = [field for field in required_fields if field not in request.data]

    if missing_fields:
        return Response({'Ошибка': f'Не хватает обязательных полей: {", ".join(missing_fields)}'}, status=status.HTTP_400_BAD_REQUEST)

    if Users.objects.filter(email=request.data['email']).exists() or Users.objects.filter(login=request.data['login']).exists():
        return Response({'Ошибка': 'Пользователь с таким email или login уже существует'}, status=status.HTTP_400_BAD_REQUEST)

    Users.objects.create(
        first_name=request.data['first_name'],
        last_name=request.data['last_name'],
        email=request.data['email'],
        login=request.data['login'],
        password=request.data['password'],
        role = request.data['role'],
    )
    return Response(status=status.HTTP_201_CREATED)

@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'login': openapi.Schema(type=openapi.TYPE_STRING, description='Логин пользователя'),
            'password': openapi.Schema(type=openapi.TYPE_STRING, description='Пароль пользователя'),
        },
        required=['login', 'password'],
    ),
    responses={
        200: openapi.Response(description='Успешная авторизация', schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={'user_id': openapi.Schema(type=openapi.TYPE_INTEGER)})),
        400: openapi.Response(description='Неверные параметры запроса или отсутствуют обязательные поля'),
        401: openapi.Response(description='Неавторизованный доступ'),
    },
    operation_description='Метод для авторизации',
)
@api_view(['POST'])
def login_view(request, format=None):
    existing_session = request.COOKIES.get('session_key')
    if existing_session and get_value(existing_session):
        return Response({'user_id': get_value(existing_session)})
        '''return Response({'user_id': get_value(existing_session), 'session_key': existing_session})'''

    login_ = request.data.get("login")
    password = request.data.get("password")
    
    if not login_ or not password:
        return Response({'error': 'Необходимы логин и пароль'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = Users.objects.get(login=login_)
    except Users.DoesNotExist:
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    if password == user.password:
        random_part = secrets.token_hex(8)
        session_hash = hashlib.sha256(f'{user.user_id}:{login_}:{random_part}'.encode()).hexdigest()
        set_key(session_hash, user.user_id)

        '''response = JsonResponse({'user_id': user.user_id, 'session_key': session_hash})'''
        response = JsonResponse({'user_id': user.user_id})
        response.set_cookie('session_key', session_hash, max_age=86400)
        return response

    return Response(status=status.HTTP_401_UNAUTHORIZED)

@swagger_auto_schema(
    method='get',
    responses={
        200: openapi.Response(description='Успешный выход', schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={'message': openapi.Schema(type=openapi.TYPE_STRING)})),
        401: openapi.Response(description='Неавторизованный доступ', schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={'error': openapi.Schema(type=openapi.TYPE_STRING)})),
    },
    operation_description='Метод для выхода пользователя из системы',
)
@api_view(['GET'])
def logout_view(request):
    session_key = request.COOKIES.get('session_key')

    if session_key:
        if not get_value(session_key):
            return JsonResponse({'error': 'Вы не авторизованы'}, status=status.HTTP_401_UNAUTHORIZED)
        delete_value(session_key)
        response = JsonResponse({'message': 'Вы успешно вышли из системы'})
        response.delete_cookie('session_key')
        return response
    else:
        return JsonResponse({'error': 'Вы не авторизованы'}, status=status.HTTP_401_UNAUTHORIZED)
    
# @api_view(['GET'])
def login_view_get(request, format=None):
    existing_session = request.COOKIES.get('session_key')
    if existing_session and get_value(existing_session):
        return Response({'user_id': get_value(existing_session)})
    return Response(status=status.HTTP_401_UNAUTHORIZED)

@swagger_auto_schema(method='get', operation_summary="Get Calculations List", responses={200: CalculationTypesSerializer(many=True)})
@api_view(['Get'])
def get_calculations_list(request, format=None):
    """
    Возвращает список операций
    """
    try:
        #inserted_application = get_object_or_404(ApplicationForCalculation,application_status="Inserted")
        user = check_authorize(request)
        print('aaa')
        if user and check_user(request):
            print('bbb')
            inserted_application = ApplicationForCalculation.objects.filter(Q(application_status="Inserted") & Q(user=user))
        else:
            inserted_application = None
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
        '''my_dict = [f'inserted application id = {inserted_application.application_id}', serializer.data]'''
        my_dict = {"inserted_application_id":inserted_application.application_id, "calculations": serializer.data}
        return Response(my_dict, template_name='tort')
    # my_dict = [serializer.data]
    # my_dict = {"calculations": serializer.data}
    my_dict = {"inserted_application_id":None, "calculations": serializer.data}
    return Response(my_dict, template_name='tort')
    # return Response(serializer.data, template_name='tort')

@swagger_auto_schema(method='get', operation_summary="Get Calculation Detailed", responses={200: CalculationTypesSerializer()})
@api_view(['Get'])
def get_calculations_detailed(request, pk, format=None):
    """
    Возвращает данные конкретной операции
    """

    '''calculation_type = get_object_or_404(CalculationTypes, pk=pk)
    if calculation_type.calculation_status == "Deleted":
        calculation_type = {}'''
    calculation_type = CalculationTypes.objects.filter(calculation_id=pk, calculation_status="Active").first()
    if request.method == 'GET':
        serializer = CalculationTypesSerializer(calculation_type)
        return Response(serializer.data)

# not used ??????
@api_view(["Post"])
def create_calculation_type_s(request, format=None):
    serializer = CalculationTypesSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(method='post', operation_summary="Create Calculation Type", request_body=CalculationTypesSerializer, responses={201: CalculationTypesSerializer()})
@api_view(["Post"])
def create_calculation_type(request, format=None):
    if not check_authorize(request) or not check_moderator(request):
        return Response({'error403':'Нет доступа'}, status=status.HTTP_403_FORBIDDEN)
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

@swagger_auto_schema(method='POST', operation_summary="Add Calculation Type to Application", request_body=CalculationTypesSerializer, responses={200: 'OK', 404: 'Операция для вычислений не найдена', 403: 'Нет доступа'})
@api_view(["POST"])
def add_calculation_type(request, pk, format=None):
    if not check_authorize(request) or not check_user(request):
        return Response({'error403':'Нет доступа'}, status=status.HTTP_403_FORBIDDEN)
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
                return Response({'error': 'Операция для вычислений не найдена'}, status=status.HTTP_404_NOT_FOUND)

            calculation_status = calculation_type.calculation_status
            print(calculation_status)
            if calculation_status != "Active":
                return Response({'error': 'Операция для вычислений не найдена'}, status=status.HTTP_404_NOT_FOUND)
            appplication_calculation = ApplicationsCalculations.objects.filter(calculation_id=calculation_id, application_id=inserted_application.application_id)
            if appplication_calculation:
                return Response({'error403':'В заявке уже есть эта операция'}, status=status.HTTP_403_FORBIDDEN)
            ApplicationsCalculations.objects.create(calculation_id=calculation_id, application_id=inserted_application.application_id)

        return Response({'message': 'Вид вычислительной операции добавлен в существующую введённую заявку'}, status=status.HTTP_200_OK)
    else:
        print('here')
        current_user = Users.objects.get(user_id=2) #????????
        print('here0')
        new_application = ApplicationForCalculation.objects.create(
            user=current_user,
            application_status='Inserted',
            date_application_create=datetime.now(),
            moderator_id=1,
            input_first_param=1,
            input_second_param=2
        )
        print('here1')
        #calculation_id = request.data['calculation_id']
        print(f"calculation_id = {calculation_id}")
        if calculation_id:
            try:
                calculation_type = CalculationTypes.objects.get(calculation_id=calculation_id)
                ApplicationsCalculations.objects.create(calculation_id=calculation_id, application_id=new_application.application_id)
            except CalculationTypes.DoesNotExist:
                new_application.delete()  
                return Response({'error': 'Операция для вычислений не найдена'}, status=status.HTTP_404_NOT_FOUND)

        return Response({'message': 'Новая заявка сформирована с операцией на вычисление'}, status=status.HTTP_201_CREATED)
    
@swagger_auto_schema(method='PUT', operation_summary="Change Calculation Type Data", request_body=CalculationTypesSerializer, responses={200: CalculationTypesSerializer(), 400: 'Bad Request'})
@api_view(["PUT"])
def change_calculation_type_data(request, pk, format=None):
    if not check_authorize(request) or not check_moderator(request):
        return Response({'error403':'Нет доступа'}, status=status.HTTP_403_FORBIDDEN)
    calculation_type = get_object_or_404(CalculationTypes, pk=pk)
    serializer = CalculationTypesSerializer(calculation_type, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(method='PUT', operation_summary="Change Calculation Type Image", request_body=CalculationTypesSerializer, responses={200: CalculationTypesSerializer(), 400: 'Bad Request'})   
@api_view(["PUT"])
def change_calculation_image(request, pk, format=None):
    if not check_authorize(request) or not check_moderator(request):
        return Response({'error403':'Нет доступа'}, status=status.HTTP_403_FORBIDDEN)
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

@swagger_auto_schema(method='DELETE', operation_summary="Delete Calculation Type", responses={204: 'No Content'})
@api_view(["Delete"])
def delete_calculation(request, pk, format=None):
    if not check_authorize(request) or not check_moderator(request):
        return Response({'error403':'Нет доступа'}, status=status.HTTP_403_FORBIDDEN)
    calculation_type = get_object_or_404(CalculationTypes, pk=pk)
    calculation_type.calculation_status = "Deleted"
    calculation_type.save()
    return Response(status=status.HTTP_204_NO_CONTENT)

@swagger_auto_schema(method='GET', operation_summary="Get Applications List", responses={200: ApplicationSerializer(many=True)})
@api_view(["Get"])
def get_applications_list(request, format=None):
    user = check_authorize(request)
    print('aaaaaaaaaaa')
    if not user:
        return Response({'error403': 'Нет доступа'}, status=drf_status.HTTP_403_FORBIDDEN)
    print(request.data)
    '''start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    status = request.GET.get('status')'''
    data = request.data

    if 'start_date' in data:
        #if data['start_date']:
        start_date = data['start_date']
    else:
        start_date = None
    if 'end_date' in data:
        end_date = data['end_date']
    else:
        end_date = None
    if 'status' in data:
        # if data['status']:
        status = data['status']
    else:
        status = None
    print(start_date)
    print(end_date)
    print(status)
    if check_moderator(request):
        # if user.role == 'Moderator':
        applications_list = ApplicationForCalculation.objects.all()
        if (status or start_date or end_date):
            if start_date:
                applications_list = applications_list.filter(Q(date_application_create__gte=start_date) & (Q(application_status="In service") | Q(application_status="Finished") | Q(application_status="Cancelled")))
                print(type(applications_list))
            if end_date:
                applications_list = applications_list.filter(Q(date_application_create__lte=end_date) & (Q(application_status="In service") | Q(application_status="Finished") | Q(application_status="Cancelled")))
            if status:
                print("aaaa")
                if status in ["Cancelled", "Finished", "In service"]:
                    applications_list = applications_list.filter(Q(application_status=status) & (Q(application_status="In service") | Q(application_status="Finished") | Q(application_status="Cancelled")))
        else:
            applications_list = ApplicationForCalculation.objects.filter((Q(application_status="Finished") | Q(application_status="In service") | Q(application_status="Cancelled")))
                
        print('here')
        applications_list = applications_list.order_by('-date_application_create')
        print('here1')
        serializer = ApplicationSerializer(applications_list, many=True)
        return Response(serializer.data)
    else:
        applications_list = ApplicationForCalculation.objects.filter((Q(application_status="Finished") | Q(application_status="In service") | Q(application_status="Cancelled")) & Q(user=user)) # user_id = application.user ????????
        if start_date:
            applications_list = applications_list.filter(date_application_create__gte=start_date)
        if end_date:
            applications_list = applications_list.filter(date_application_create__lte=end_date)

        applications_list = applications_list.order_by('-date_application_create')
        serializer = ApplicationSerializer(applications_list, many=True)
        return Response(serializer.data)

@swagger_auto_schema(method='GET', operation_summary="Get Application Detail", responses={200: ApplicationSerializer()}) # разве ,этот сериализатор????????
@api_view(["Get"])
def get_application_detailed(request, pk, format=None):
    user = check_authorize(request)
    if not user:
        return Response({'error403': 'Нет доступа'}, status=drf_status.HTTP_403_FORBIDDEN)
    if check_user(request):
        # application = get_object_or_404(ApplicationForCalculation, pk=pk, user=user)
        print(user)
        application = ApplicationForCalculation.objects.filter(Q(application_id=pk) & Q(user=user)).first()
    else:
        application = get_object_or_404(ApplicationForCalculation, pk=pk)

    if application is None:
        return Response({'error': 'Заявка не найдена'}, status=status.HTTP_404_NOT_FOUND)
    serializer = ApplicationSerializer(application)
    applications_calculations = ApplicationsCalculations.objects.filter(application_id=pk)
    serializer_apps_calcs = ApplicationsCalculationsSerializer(applications_calculations, many=True)

    filters = Q()
    print("aaaa")
    for app_calc in applications_calculations:
        filters |= Q(calculation_id=app_calc.calculation_id)
    print(filters)
    if filters != Q():
        calculation_type = CalculationTypes.objects.filter(filters)
    else:
        calculation_type = {}
    serializer_calc_types = CalculationTypesSerializer(calculation_type, many=True)
    apps_calcs_data = {
        'application': serializer.data,
        'calculation': serializer_calc_types.data
    }
    return Response(apps_calcs_data)
    #return Response(serializer.data)

@swagger_auto_schema(method='PUT', operation_summary="Change Input Arguments", responses={200: ApplicationDetailedSerializer(), 400: 'Bad Request', 403: 'Forbidden'})
@api_view(['PUT'])
def change_inputs_application(request, pk, format=None):
    """
    Обновляет информацию в заявке - input arguments
    """
    if not check_authorize(request) or not check_user(request):
        return Response({'error403':'Нет доступа'}, status=status.HTTP_403_FORBIDDEN)
    print('aaaaaaa')
    application = get_object_or_404(ApplicationForCalculation, pk=pk)
    print('bbbbb')
    if application.application_status != 'Inserted':
        return Response({"error": "Неверный статус."}, status=400)
    if request.data['input_first_param'] and request.data['input_first_param'] != application.input_first_param:
        application.input_first_param = request.data['input_first_param']
    print('cccccccc')
    if request.data['input_second_param'] and request.data['input_second_param'] != application.input_second_param:
        application.input_second_param = request.data['input_second_param']
    print('dddddd')
    #serializer = ApplicationDetailedSerializer(application, data=request.data, partial=True) #AplSer
    serializer = ApplicationSerializer(application, data=request.data, partial=True)
    print('eeeeeee')
    if serializer.is_valid():
        print('fffff')
        serializer.save()
        print('ggggg')
        return Response(serializer.data)
    print('hhhhhhh')
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(method='DELETE', operation_summary="Delete Calculation Type From Application", responses={200: ApplicationDetailedSerializer(), 400: 'Bad Request'})
@api_view(["DELETE"])
def delete_calculation_from_application(request, application_id,
                                        calculation_id, format=None):
    if not check_authorize(request) or not check_user(request):
        return Response({'error403':'Нет доступа'}, status=status.HTTP_403_FORBIDDEN)
    application = get_object_or_404(ApplicationForCalculation, pk=application_id)

    applications_calculations = get_object_or_404(ApplicationsCalculations, application_id=application, calculation_id=calculation_id)

    applications_calculations.delete()

    serializer = ApplicationDetailedSerializer(application) #AplSer
    return Response(serializer.data, status=status.HTTP_200_OK)

@swagger_auto_schema(method='DELETE', operation_summary="Delete Application", responses={204: 'Заявка успешно удалена'})
@api_view(["DELETE"])
def delete_application_for_calculation(request, application_id, format=None):
    if not check_authorize(request) or not check_user(request):
        return Response({'error403':'Нет доступа'}, status=status.HTTP_403_FORBIDDEN)
    application = get_object_or_404(ApplicationForCalculation,
                                    pk=application_id)
    if application.application_status != 'Inserted':
        return Response({"error": "Неверный статус."}, status=400)
    user_id = request.query_params.get('user_id')
    print(user_id)

    try:
        user = Users.objects.get(user_id=user_id)
        if user.role != 'Moderator':
            return Response({'error': 'У пользователя нет статуса "модератор"'}, status=status.HTTP_403_FORBIDDEN)
    except Users.DoesNotExist:
        return Response({'error': 'Пользователь не найден'}, status=status.HTTP_404_NOT_FOUND)

    application.application_status = 'Deleted'
    application.save()

    return Response({'message': 'Заявка успешно удалена'}, status=status.HTTP_204_NO_CONTENT)


@swagger_auto_schema(method='PUT', operation_summary="Change Status (Moderator)", responses={200: 'OK', 403: 'Неверный статус', 400: 'Bad Request'})
@api_view(['PUT']) 
def put_applications_moderator(request, pk, format=None):
    """
    Обновляет информацию о заявке модератором
    """
    if not check_authorize(request) or not check_moderator(request):
        return Response({'error403':'Нет доступа'}, status=status.HTTP_403_FORBIDDEN)
    application = get_object_or_404(ApplicationForCalculation, pk=pk)
    print(application.application_status)
    print(f'_______{request.data}__________')
    if 'application_status' in request.data:
        print(request.data['application_status'])
    else:
        return Response({"error": "Новый статус не передан"}, status=403)
    print(application.application_status)
    if request.data['application_status'] not in ['Finished', 'Canceled'] or application.application_status == 'Inserted':
        print('aaaa')
        return Response({"error": "Неверный статус."}, status=403)
    print('bbbb')
    application.application_status = request.data['application_status']
    print('ccccc')
    application.date_application_complete = datetime.now()
    print('dddddd')
    serializer = ApplicationSerializer(application, data=request.data, partial=True)
    print('fffff')
    if serializer.is_valid():
        print('ggggg')
        serializer.save()
        return Response(serializer.data)
    print('hhhhhh')
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(method='PUT', operation_summary="Change Status (User)", responses={200: 'OK', 403: 'Неверный статус', 400: 'Bad Request'})
@api_view(['PUT']) 
def put_applications_client(request, pk, format=None):
    """
    Обновляет информацию о заявке клиентом
    """
    if not check_authorize(request) or not check_user(request):
        return Response({'error403':'Нет доступа'}, status=status.HTTP_403_FORBIDDEN)
    application = get_object_or_404(ApplicationForCalculation, pk=pk)
    print(f'_______{request.data}__________')
    print('aaaaaaa')
    print(request.data['application_status'])
    print(application.application_status)
    if request.data['application_status'] != 'In service' or application.application_status != 'Inserted':
        return Response({"error": "Неверный статус."}, status=403)
    print("ssssss")

    try:
        applications_calculations = ApplicationsCalculations.objects.filter(application=pk)
        print('am1')
        post_url = "http://localhost:8080/api/calculate_operations/"
        calc_req_data = {
                        "id": application.application_id,
                        "input_first_param": application.input_first_param,
                        "input_second_param": application.input_second_param,
                        "calculations": [
                            {"calculation_id": applic_calc.calculation.calculation_id} for applic_calc in applications_calculations
                        ]
        }
        print('am2')
                   
        response_post = requests.post(post_url, json=calc_req_data)
        print('am3')
        response_post.raise_for_status()
        print('am4')

    except Exception as e:
        print('ВЫчислительный сервис не отвечает')
        print(e)
    application.application_status = request.data['application_status']
    print("ffffff")
    application.date_application_accept = datetime.now()
    print("wwwwwww")
    serializer = ApplicationSerializer(application, data=request.data, partial=True)
    print("oooooo")
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@parser_classes([JSONParser])
def write_calculating_result(request, format=None):
    try:
        data = request.data
        if not data["token"] or data["token"] != "Hg45ArLPEqiQ7-weSrTGo":
            print('Forbidden')
            return Response(status=status.HTTP_403_FORBIDDEN)

        application_id = data["application_id"]
        for result_data in data["results"]:
            calculation_id = result_data["calculation_id"]

            applications_calculations = ApplicationsCalculations.objects.filter(application=application_id, calculation=calculation_id)

            if applications_calculations:
                print('i am here')
                print(f'!!!!!{result_data["output_param"]}!!!')
                if result_data["output_error_param"] != '':
                    print(f'error with result from async : {result_data["output_error_param"]}')
                    return Response(status=status.HTTP_400_BAD_REQUEST)
                applications_calculations.update(result=result_data["output_param"])
                print('I am here 2')
                '''application = ApplicationForCalculation.objects.get(pk=application_id)
                application.status_application = "Finished"
                application.date_application_complete = timezone.now()
                application.save()'''

        return Response(status=status.HTTP_200_OK)

    except Exception as e:
        print(e)
        return Response(status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(method='PUT', operation_summary="Update Application", responses={200: 'Успешно', 404: 'Не найдено', 400: 'Bad Request'})
@api_view(['PUT'])
def edit_result_applications_calculations(request, pk, calculation_id, format=None):
    print('zzzzzz')
    if not check_authorize(request) or not check_moderator(request):
        print('ggggg')
        return Response({'error403':'Нет доступа'}, status=status.HTTP_403_FORBIDDEN)
    try:
        new_result = request.data.get('new_result')
        print('a')
        application_calculation = ApplicationsCalculations.objects.filter(application=pk, calculation=calculation_id)
        print('b')
        if application_calculation:
            print('aaa')
            # application_calculation.result = new_result
            application_calculation.update(result=new_result)
            print('bbbbb')
            serializer = ApplicationsCalculationsSerializer(application_calculation, data=request.data, partial=True)
            print('cccccc')
            #return Response(serializer.data)
            print('c')
            return Response({"response": "Успешно"}, status=status.HTTP_200_OK)
        else:
            print('d')
            return Response({"Не найдено"}, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        print('e')
        return Response(str(e), status=status.HTTP_400_BAD_REQUEST)