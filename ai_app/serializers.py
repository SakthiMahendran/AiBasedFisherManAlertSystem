from rest_framework import serializers

class FileAnalyzerSerializer(serializers.Serializer):
    """
    Serializer to validate uploaded files for supported types and size.
    """
    file = serializers.FileField()

    def validate_file(self, file):
        # Allowed MIME types
        valid_mime_types = [
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "text/plain",
        ]

        # Validate MIME type
        if file.content_type not in valid_mime_types:
            raise serializers.ValidationError(
                "Unsupported file format. Supported formats: PDF, DOC, DOCX, TXT."
            )

        # Validate file size (limit: 5MB)
        if file.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("File size exceeds 5MB.")

        return file
