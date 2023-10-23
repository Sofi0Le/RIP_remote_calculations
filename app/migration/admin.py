from django.contrib import admin

from app.migration import models


admin.site.register(models.ApplicationForCalculation)
admin.site.register(models.ApplicationsCalculations)
admin.site.register(models.CalculationTypes)
admin.site.register(models.Users)