{{- define "common.config" -}}
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "common.fullname" . }}
data:
  # Postgres
  POSTGRES__USERNAME: infanasotku
  POSTGRES__DATABASE: {{ .Values.config.POSTGRES__DATABASE }}
  POSTGRES__HOST: local.infanasotku.com.
  POSTGRES__PORT: "5430"
{{- end }}
