'''from django.http import HttpResponse

def hello(request):
    return HttpResponse('Hello world!')'''

from django.shortcuts import render

'''def hello(request):
    return render(request, 'index.html')'''

from datetime import date

db_operations = {
    'operations_to_perform': [
        {
            'id': 0,
            'type': 'Факториал',
            'description': 'Факториал натурального числа n определяется как произведение всех натуральных чисел от 1 до n включительно.',
            'image_url': '../static/images/5fca1b8b21ecb465077855.png'
        },
        {
            'id': 1,
            'type': 'НОД',
            'description': 'Наибольшим общим делителем (НОД) для двух целых чисел m и n называется наибольший из их общих делителейю.  Пример: для чисел 84 и 90 наибольший общий делитель равен 6. Наибольший общий делитель существует и однозначно определён, если хотя бы одно из чисел m или n не равно нулю.',
            'image_url': '../static/images/5fb67e6f84777264696784.png'
        },
        {
            'id': 2,
            'type': 'НОК',
            'description': 'Наименьшее общее кратное (НОК) двух целых чисел m и n есть наименьшее натуральное число, которое делится на m и n без остатка, то есть кратно им обоим. Пример: HOK(36, 48) = 144.',
            'image_url': '../static/images/NOK.png'
        },
        {
            'id': 3,
            'type': 'Число Фибоначи',
            'description': 'Числа Фибоначчи (строка Фибоначчи) — числовая последовательность, первые два числа которой являются 0 и 1, а каждое последующее за ними число является суммой двух предыдущих.',
            'image_url': '../static/images/Fibonacci.png'
        },
        {
            'id': 4,
            'type': 'Сложение матриц',
            'description': 'Сложение матриц А и В – это нахождение такой матрицы С , все элементы которой представляют собой сложенные попарно соответствующие элементы исходных матриц А и В.',
            'image_url': '../static/images/pict001.png'
        },
        {
            'id': 5,
            'type': 'Умножение матриц',
            'description': 'Умножение матриц — одна из основных операций над матрицами. Матрица, получаемая в результате операции умножения, называется произведением ма́триц. Элементы новой матрицы получаются из элементов старых матриц в соответствии с правилами, проиллюстрированными левее.',
            'image_url': '../static/images/Matrix_multiplication.png'
        }
    ]
}


def detailed_operations_page(request, id):
    data_by_id = db_operations.get('operations_to_perform')[id]
    return render(request, 'operation_types_detailed.html', {
        'operations_to_perform': data_by_id
    })

def operations_page(request):
    query = request.GET.get('q')

    if query:
        # Фильтрую данные, при этом учитываю поле "type"
        filtered_data = [item for item in db_operations['operations_to_perform'] if
                         query.lower() in item['type'].lower()]

    else:
        filtered_data = db_operations['operations_to_perform']
        query = ""
  

    return render(request, "operation_types.html", {'filtered_data': filtered_data, 'search_value': query})
