from django.db import models


class ApplicationForCalculation(models.Model):
    application_id = models.AutoField(primary_key=True)
    user = models.ForeignKey('Users', models.DO_NOTHING, db_column='user')
    date_application_create = models.DateField(blank=True, null=True)
    date_application_accept = models.DateField(blank=True, null=True)
    date_application_complete = models.DateField(blank=True, null=True)
    application_status = models.TextField()  # This field type is a guess.

    class Meta:
        managed = False
        db_table = 'application_for_calculation'


class ApplicationsCalculations(models.Model):
    application = models.ForeignKey(ApplicationForCalculation, models.DO_NOTHING, db_column='application')
    calculation = models.ForeignKey('CalculationTypes', models.DO_NOTHING, db_column='calculation')

    class Meta:
        managed = False
        db_table = 'applications_calculations'


class CalculationTypes(models.Model):
    calculation_id = models.AutoField(primary_key=True)
    calculation_name = models.CharField(max_length=30)
    calculation_description = models.CharField(max_length=1500)
    calculation_image_url = models.CharField(max_length=50, blank=True, null=True)
    calculation_status = models.TextField()  # This field type is a guess.

    class Meta:
        managed = False
        db_table = 'calculation_types'


class Users(models.Model):
    user_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=20)
    last_name = models.CharField(max_length=40)
    email = models.CharField(unique=True, max_length=30, blank=True, null=True)
    login = models.CharField(unique=True, max_length=40, blank=True, null=True)
    password = models.CharField(unique=True, max_length=30, blank=True, null=True)
    role = models.CharField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'users'