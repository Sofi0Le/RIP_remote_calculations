'''from django.http import HttpResponse

def hello(request):
    return HttpResponse('Hello world!')'''

from django.shortcuts import render, redirect
from django.db import connection
from django.urls import reverse
from django.db.models import Q

'''def hello(request):
    return render(request, 'index.html')'''

from datetime import date
from migrations import models



'''def detailed_operations_page(request, id):
    data_by_id = db_operations.get('operations_to_perform')[id]
    return render(request, 'operation_types_detailed.html', {
        'operations_to_perform': data_by_id
    })
'''

def detailed_operations_page(request, id):
     return render(request, 'operation_types_detailed.html', {
        'operations_to_perform' : models.CalculationTypes.objects.filter(calculation_id=id).first()
    })

def operations_page(request):
    query = request.GET.get('q')

    if query:
        # Фильтрую данные, при этом учитываю поле "type"
        filtered_data = {'operations_to_perform': models.CalculationTypes.objects.filter(Q(modeling_name__icontains=query))}

    else:
        filtered_data = {'operations_to_perform': models.CalculationTypes.objects.all()}

        query = ""
  
    return render(request, "operation_types.html", {'filtered_data': filtered_data})
