from rest_framework import serializers
from app.migration.models import CalculationTypes
from app.migration.models import ApplicationForCalculation
from app.migration.models import Users
from app.migration.models import ApplicationsCalculations

class CalculationTypesSerializer(serializers.ModelSerializer):
    full_url = serializers.SerializerMethodField()

    def get_full_url(self, obj):
        image_url = obj.calculation_image_url
        custom_value = f"http://192.168.0.46:9000/pictures/{image_url}" # for 7th laba use ip addres 172.20.10.11 for example
        return custom_value
    class Meta:
        # Модель, которую мы сериализуем
        model = CalculationTypes
        # Поля, которые мы сериализуем
        fields = [
            "calculation_id",
            "calculation_name",
            "calculation_description",
            "calculation_status",
            "full_url"
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
        model = ApplicationsCalculations
        # Поля, которые мы сериализуем
        fields = [
            "application_id",
            "calculation",
            "result",
        ]
        
        '''"calculation_id"
        result'''
        
class ApplicationDetailedSerializer(serializers.ModelSerializer):
    user = UsersSerializer(read_only=True)
    calculation_detailes = serializers.SerializerMethodField()

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

    def get_calculation_detailes(self, obj):
        # Retrieve the specific ApplicationsCalculations object you want to include
        # For example, get the first one (you might want to adjust this logic based on your requirements)
        applications_calculations_instance = ApplicationsCalculations.objects.filter(application=obj)
        
        # Serialize the specific ApplicationsCalculations instance
        if applications_calculations_instance:
            return ApplicationsCalculationsSerializer(applications_calculations_instance).data
        else:
            return None
