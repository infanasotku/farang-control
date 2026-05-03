{{- define "common.config" -}}
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "common.fullname" . }}
data:
  ENV: {{ .Values.config.ENV }}

  # Admin
  ADMIN__USERNAME: admin
{{- end }}
