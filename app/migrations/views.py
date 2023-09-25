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
