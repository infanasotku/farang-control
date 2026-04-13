{{- define "common.config" -}}
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "common.fullname" . }}
data:
  ENV: {{ .Values.config.ENV }}

  # Postgres
  POSTGRES__USERNAME: infanasotku
  POSTGRES__DATABASE: {{ .Values.config.POSTGRES__DATABASE }}
  POSTGRES__HOST: local.infanasotku.com.
  POSTGRES__PORT: "5430"

  # Admin
  ADMIN__USERNAME: admin
{{- end }}
