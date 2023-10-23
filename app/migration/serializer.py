from rest_framework import serializers
from app.migration.models import CalculationTypes
from app.migration.models import ApplicationForCalculation
from app.migration.models import Users
from app.migration.models import ApplicationsCalculations

class CalculationTypesSerializer(serializers.ModelSerializer):
    class Meta:
        # Модель, которую мы сериализуем
        model = CalculationTypes
        # Поля, которые мы сериализуем
        fields = [
            "calculation_id",
            "calculation_name",
            "calculation_description",
            "calculation_status"
        ]

class UsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = [
            "user_id",
            "first_name",
            "last_name",
            "email",
            "login",
            "password",
            "role"
        ]


class ApplicationSerializer(serializers.ModelSerializer):
    user = UsersSerializer(read_only=True)

    class Meta:
        model = ApplicationForCalculation
        fields = [
            "application_id",
            "user",
            "date_application_create",
            "date_application_accept",
            "date_application_complete",
            "application_status",
            "moderator_id",
            "input_first_param",
            "input_second_param"
        ]
        '''"input_first_param",
            "input_second_param"'''
        
class ApplicationsCalculationsSerializer(serializers.ModelSerializer):
    calculation = CalculationTypesSerializer()
    class Meta:
        # Модель, которую мы сериализуем
        model = CalculationTypes
        # Поля, которые мы сериализуем
        fields = [
            "application_id",
            "calculation"
        ]
        
        '''"calculation_id"
        result'''
        
class ApplicationDetailedSerializer(serializers.ModelSerializer):
    user = UsersSerializer(read_only=True)
    calculation_detailes = ApplicationsCalculationsSerializer(many=True, source='applicationscalculations_set')

    class Meta:
        model = ApplicationForCalculation
        fields = [
            "application_id",
            "user",
            "date_application_create",
            "date_application_accept",
            "date_application_complete",
            "application_status",
            "moderator_id",
            "input_first_param",
            "input_second_param",
            "calculation_detailes",
        ]
        '''"input_first_param",
            "input_second_param"'''
