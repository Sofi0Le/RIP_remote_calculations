'''
from django.shortcuts import render, redirect
from django.db import connection
from django.urls import reverse
import psycopg2

from app.migrations import models

def detailed_operations_page(request, id):
     return render(request, 'operation_types_detailed.html', {
        'operations_to_perform' : models.CalculationTypes.objects.filter(calculation_id=id).first()
    })

def operations_page(request):
    query = request.GET.get('q')

    if query:
        # Фильтрую данные, при этом учитываю поле "calculation_name"
        filtered_data = {'operations_to_perform': models.CalculationTypes.objects.filter(calculation_name__icontains=query, calculation_status="Active")}

    else:
        filtered_data = {'operations_to_perform': models.CalculationTypes.objects.filter(calculation_status="Active")}

        query = ""
    return render(request, "operation_types.html", {'filtered_data': filtered_data, 'search_value': query})

def delete_operation(id):
    conn = psycopg2.connect(dbname="remote_calculations", host="localhost", user="sofi_w", password="sleep", port="5432")
    with conn:
        with conn.cursor() as cursor:
        
            quarry = f"UPDATE calculation_types SET calculation_status = 'Deleted' WHERE calculation_id = %s"
            cursor.execute(quarry, [id])
        
            conn.commit()   # реальное выполнение команд sql1
        
        cursor.close()
    conn.close()

def update_operations_page(request, id):
    conn = psycopg2.connect(dbname="remote_calculations", host="localhost", user="sofi_w", password="sleep", port="5432")
    with conn:
        with conn.cursor() as cursor:
        
            quarry = f"UPDATE calculation_types SET calculation_status = 'Deleted' WHERE calculation_id = %s"
            cursor.execute(quarry, [id])
        
            conn.commit()   # реальное выполнение команд sql1

    return redirect('/')#просто delete
    #return render(request, "operation_types.html")
    '''
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

from rest_framework.decorators import api_view
from datetime import datetime

MANAGER_ID = 1
USER_ID = 2

@api_view(['Get'])
def get_calculations_list(request, format=None):
    """
    Возвращает список операций
    """
    print('get')
    query = request.GET.get("title")
    if query:
        calculation_types = CalculationTypes.objects.filter(calculation_name__icontains=query, calculation_status="Active")
    else:
        calculation_types = CalculationTypes.objects.filter(calculation_status="Active")
    serializer = CalculationTypesSerializer(calculation_types, many=True)
    return Response(serializer.data)

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
def create_calculation_type(request, format=None):
    serializer = CalculationTypesSerializer(data=request.data)
    if serializer.is_valid():
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

@api_view(["Delete"])
def delete_calculation(request, pk, format=None):
    calculation_type = get_object_or_404(CalculationTypes, pk=pk)
    calculation_type.calculation_status = "Deleted"
    calculation_type.save()
    return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(["Get"])
def get_applications_list(request, format=None):

    start_date = request.GET.get('start_date', None)
    end_date = request.GET.get('end_date', None)
    status = request.GET.get('status', None)
    
    applications_list = ApplicationForCalculation.objects.all()

    if start_date:
        applications_list = applications_list.filter(date_application_create__gte=start_date)
        if end_date:
            applications_list = applications_list.filter(date_application_create__lte=end_date)
    if status:
        applications_list = applications_list.filter(application_status=status)

    applications_list = applications_list.order_by('-date_application_create')
    serializer = ApplicationSerializer(applications_list, many=True)
    return Response(serializer.data)

@api_view(["Get"])
def get_application_detailed(request, pk, format=None):
    application = get_object_or_404(ApplicationForCalculation, pk=pk)
    serializer = ApplicationDetailedSerializer(application)

    return Response(serializer.data)
'''
@api_view(["PUT"])
def change_inputs(request, application_id, calculation_id, format=None):
    application = get_object_or_404(ApplicationForCalculation, pk=application_id)

    applications_calculations = get_object_or_404(ApplicationsCalculations, application=application, calculation_id=calculation_id)

    first_input, second_input = request.data.get('first_input', 'second_input')
    if first_input is not None and second_input is not None:
        applications_calculations.q= new_quantity
        bouquet_application.save()

        serializer = ApplicationSerializer(service_application)
        return Response(serializer.data, status=status.HTTP_200_OK)
    else:
        return Response({'error': 'Quantity is required'}, status=status.HTTP_400_BAD_REQUEST)
'''

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
    serializer = ApplicationSerializer(application, data=request.data, partial=True)
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

    serializer = ApplicationSerializer(application)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(["DELETE"])
def delete_application_for_calculation(request, application_id, format=None):
    application = get_object_or_404(ApplicationForCalculation,
                                    pk=application_id)
    if application.application_status != 'Inserted':
        return Response({"error": "Неверный статус."}, status=400)
    user_id = request.query_params.get('user_id')

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