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
            "calculation_image_url",
            "full_url"
        ]

class CalculationTypesSerializerNew(serializers.ModelSerializer):
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
            "full_url",
            "result"
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
    moderator = UsersSerializer(read_only=True)

    class Meta:
        model = ApplicationForCalculation
        fields = [
            "application_id",
            "user",
            "date_application_create",
            "date_application_accept",
            "date_application_complete",
            "application_status",
            "moderator",
            "input_first_param",
            "input_second_param"
        ]
        '''"input_first_param",
            "input_second_param"'''
        
class ApplicationNewSerializer(serializers.ModelSerializer):
    user_login = serializers.CharField(source='user.login', read_only=True)
    moderator_login = serializers.CharField(source='moderator.login', read_only=True)
    count_empty_results = serializers.SerializerMethodField()

    class Meta:
        model = ApplicationForCalculation
        fields = [
            "application_id",
            "user_login",
            "date_application_create",
            "date_application_accept",
            "date_application_complete",
            "application_status",
            "moderator_login",
            "input_first_param",
            "input_second_param"
        ]

    class Meta:
        model = ApplicationForCalculation
        fields = [
            "application_id",
            "user_login",
            "date_application_create",
            "date_application_accept",
            "date_application_complete",
            "application_status",
            "moderator_login",
            "input_first_param",
            "input_second_param",
            "count_empty_results"  # Include the new field here
        ]

    def get_count_empty_results(self, obj):
        # Calculate and return the count_empty_results for the current application
        count_empty_results = ApplicationsCalculations.objects.filter(
            application=obj.application_id,
            result__isnull=False
        ).count()
        return count_empty_results
        
class ApplicationsCalculationsSerializer(serializers.ModelSerializer):
    calculation = CalculationTypesSerializer()

    class Meta:
        model = ApplicationsCalculations
        fields = [
            "application_id",
            "calculation",
            "result"  # Add the "result" field here
        ]

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
        applications_calculations_instance = ApplicationsCalculations.objects.filter(application=obj)

        if applications_calculations_instance:
            # Serialize the specific ApplicationsCalculations instance and include the "result" field
            return ApplicationsCalculationsSerializer(applications_calculations_instance, many=True).data
        else:
            return None