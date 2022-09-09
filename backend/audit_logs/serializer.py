from rest_framework import serializers
from auditlog.models import LogEntry

class AuditLogSerializer(serializers.ModelSerializer):
    '''CREATE = 0  UPDATE = 1    DELETE = 2
        Auditlog distinguishes: creating, updating and deleting objects
    '''
    Entity = serializers.SerializerMethodField()
    Username= serializers.PrimaryKeyRelatedField(read_only=True,source='actor.Name',)
    Date    =serializers.DateTimeField(source='timestamp')
    Action = serializers.IntegerField(source='action')
    Action_details= serializers.SerializerMethodField()
    Message = serializers.CharField(source='changes')
    EntityRepresentation = serializers.CharField(source='object_repr')
    EntityID = serializers.CharField(source='object_id')
    
    class Meta:
        model = LogEntry
        fields = ['EntityRepresentation','EntityID','Entity', 'EntityID','Username', 'Date', 'Action', 'Message','Action_details']
    #getting the actial model instance name
    def get_Entity(self, obj):
        return f'{obj.content_type.model_class().__name__}'

    def get_Action_details(self, obj):
        if obj.action == 0:
            return 'CREATE'
        elif obj.action == 1:
            return 'UPDATE'
        elif obj.action == 2:
            return 'DELETE'


