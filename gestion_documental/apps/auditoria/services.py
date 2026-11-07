"""
Servicios del módulo de auditoría.

Contiene la lógica de negocio para registrar y consultar actividades.
"""
from django.db import models
from django.db.models import Q
# pyrefly: ignore [missing-import]
from apps.auditoria.models import RegistroAuditoria


class AuditoriaService:
    """Servicio para la gestión de registros de auditoría."""

    @staticmethod
    def registrar(usuario, accion, documento=None, ip_address=None, detalle=''):
        """Registra una acción en el log de auditoría."""
        return RegistroAuditoria.objects.create(
            usuario=usuario,
            accion=accion,
            documento=documento,
            ip_address=ip_address,
            detalle=detalle or '',
        )

    @staticmethod
    def listar_registros(usuario=None, accion=None, documento=None, fecha_inicio=None, fecha_fin=None):
        """Lista registros de auditoría con filtros opcionales."""
        from datetime import timedelta

        from core.utils.helpers import parse_fecha_segura, inicio_dia
        queryset = RegistroAuditoria.objects.select_related(
            'usuario', 'usuario__programa_academico', 'documento', 'documento__categoria'
        ).order_by('-fecha_hora')

        if usuario:
            # Intentar filtrar por ID si es numérico, de lo contrario por nombre/email
            if usuario.isdigit():
                queryset = queryset.filter(usuario_id=usuario)
            else:
                queryset = queryset.filter(
                    Q(usuario__first_name__icontains=usuario) |
                    Q(usuario__last_name__icontains=usuario) |
                    Q(usuario__email__icontains=usuario)
                )

        if accion:
            queryset = queryset.filter(accion=accion)

        if documento:
            if documento.isdigit():
                queryset = queryset.filter(documento_id=documento)
            else:
                queryset = queryset.filter(documento__titulo__icontains=documento)

        if fecha_inicio:
            fecha_inicio = parse_fecha_segura(fecha_inicio)
        if fecha_inicio:
            # H-13: rango index-friendly en vez de __date.
            queryset = queryset.filter(fecha_hora__gte=inicio_dia(fecha_inicio))

        if fecha_fin:
            fecha_fin = parse_fecha_segura(fecha_fin)
        if fecha_fin:
            queryset = queryset.filter(
                fecha_hora__lt=inicio_dia(fecha_fin) + timedelta(days=1)
            )

        return queryset

    @staticmethod
    def obtener_historial_documento(documento_id):
        """Obtiene el historial de auditoría de un documento específico."""
        return RegistroAuditoria.objects.filter(
            documento_id=documento_id
        ).select_related('usuario').order_by('-fecha_hora')

    @staticmethod
    def generar_auditoria_excel(registros):
        """Genera un archivo Excel en memoria con los registros de auditoria."""
        import io
        import openpyxl
        from openpyxl.styles import PatternFill, Font, Border, Side, Alignment
        from django.utils import timezone

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Auditoria SIGEA"

        # Estilos corporativos
        header_fill = PatternFill(start_color="0F2044", end_color="0F2044", fill_type="solid")
        header_font = Font(color="FFFFFF", bold=True, size=11)
        
        zebra_fill_1 = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
        zebra_fill_2 = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
        
        thin_border = Border(
            left=Side(style='thin', color='E2E8F0'), 
            right=Side(style='thin', color='E2E8F0'), 
            top=Side(style='thin', color='E2E8F0'), 
            bottom=Side(style='thin', color='E2E8F0')
        )
        align_center = Alignment(horizontal='center', vertical='center')
        align_left = Alignment(horizontal='left', vertical='center', wrap_text=True)

        # 1. Título principal
        ws.merge_cells('A1:H1')
        title_cell = ws['A1']
        title_cell.value = "Reporte Oficial de Auditoría (SIGEA)"
        title_cell.font = Font(color="0F2044", bold=True, size=16)
        title_cell.alignment = align_center
        ws.row_dimensions[1].height = 30

        # 2. Subtítulo
        ws.merge_cells('A2:H2')
        subtitle_cell = ws['A2']
        fecha_str = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
        total_excel = registros.count()
        subtitle_cell.value = f"Fecha de generación: {fecha_str} | Total de registros: {total_excel}"
        subtitle_cell.font = Font(color="475569", size=10)
        subtitle_cell.alignment = align_center
        ws.row_dimensions[2].height = 20

        ws.append([]) # Espacio

        # 3. Encabezados
        headers = ['Fecha', 'Hora', 'Usuario (Email)', 'Nombre', 'Programa Académico', 'Acción', 'Documento/Descripción', 'Dirección IP']
        ws.append(headers)
        
        header_row = ws.max_row
        ws.row_dimensions[header_row].height = 25

        for col_idx, cell in enumerate(ws[header_row], 1):
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = align_center
            cell.border = thin_border

        # 4. Datos (iterator: no carga todo el queryset en memoria ORM)
        from core.utils.helpers import sanear_celda_excel
        for i, reg in enumerate(registros.iterator(chunk_size=2000)):
            fecha = reg.fecha_hora.astimezone().strftime('%d/%m/%Y')
            hora = reg.fecha_hora.astimezone().strftime('%H:%M:%S')
            email = reg.usuario.email if reg.usuario else 'Sistema'
            nombre = reg.usuario.get_full_name() if reg.usuario else '-'
            programa = reg.usuario.programa_academico.nombre if reg.usuario and hasattr(reg.usuario, 'programa_academico') and reg.usuario.programa_academico else '-'
            doc_desc = reg.documento.titulo if reg.documento else reg.detalle
            ip = reg.ip_address if reg.ip_address else '-'

            row = [fecha, hora, sanear_celda_excel(email), sanear_celda_excel(nombre),
                   sanear_celda_excel(programa), reg.get_accion_display(),
                   sanear_celda_excel(doc_desc), ip]
            ws.append(row)
            
            current_row = ws.max_row
            ws.row_dimensions[current_row].height = 20
            fill_color = zebra_fill_1 if i % 2 == 0 else zebra_fill_2
            
            for cell in ws[current_row]:
                cell.fill = fill_color
                cell.border = thin_border
                if cell.column in (3, 4, 5, 7): # Columnas de texto largo a la izquierda
                    cell.alignment = align_left
                else:
                    cell.alignment = align_center

        # Autoajustar columnas
        from openpyxl.utils import get_column_letter
        for i, col in enumerate(ws.columns, 1):
            max_length = 0
            column = get_column_letter(i)
            for cell in col:
                try:
                    if cell.row > 2 and len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = (max_length + 2)
            ws.column_dimensions[column].width = adjusted_width
            
        ws.column_dimensions['G'].width = 50 # Forzar doc_desc

        output = io.BytesIO()
        wb.save(output)
        return output.getvalue()

    @staticmethod
    def generar_auditoria_pdf(response, registros):
        """Genera un reporte PDF de auditoria utilizando ReportLab."""
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        from django.utils import timezone

        doc = SimpleDocTemplate(response, pagesize=landscape(A4), rightMargin=20, leftMargin=20, topMargin=30, bottomMargin=18)
        elements = []
        styles = getSampleStyleSheet()

        title_style = styles['Heading1']
        title_style.alignment = 1 
        title_style.textColor = colors.HexColor('#0F2044')
        elements.append(Paragraph("<b>Reporte Oficial de Auditoría (SIGEA)</b>", title_style))
        elements.append(Spacer(1, 10))

        normal_style = styles['Normal']
        fecha_str = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
        total_pdf = registros.count()
        elements.append(Paragraph(f"<b>Fecha de generación:</b> {fecha_str} | <b>Total de registros:</b> {total_pdf}", normal_style))
        elements.append(Spacer(1, 20))

        table_data = [['Fecha', 'Hora', 'Usuario', 'Acción', 'Documento/Descripción', 'IP']]
        for reg in registros.iterator(chunk_size=2000):
            fecha = reg.fecha_hora.astimezone().strftime('%d/%m/%Y')
            hora = reg.fecha_hora.astimezone().strftime('%H:%M:%S')
            usuario_str = f"{reg.usuario.get_full_name()} ({reg.usuario.email})" if reg.usuario else 'Sistema'
            doc_desc = reg.documento.titulo if reg.documento else reg.detalle
            ip = reg.ip_address if reg.ip_address else '-'
            
            table_data.append([
                fecha,
                hora,
                Paragraph(usuario_str, normal_style),
                reg.get_accion_display(),
                Paragraph(doc_desc, normal_style),
                ip
            ])
        
        col_widths = [60, 50, 200, 100, 260, 80]
        t = Table(table_data, colWidths=col_widths, repeatRows=1)
        
        header_bg = colors.HexColor('#0F2044')
        row_bg_1 = colors.HexColor('#FFFFFF')
        row_bg_2 = colors.HexColor('#F8FAFC')
        grid_color = colors.HexColor('#E2E8F0')

        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), header_bg),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
            ('ALIGN', (2, 1), (2, -1), 'LEFT'), # Usuario
            ('ALIGN', (4, 1), (4, -1), 'LEFT'), # Doc/Desc
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [row_bg_1, row_bg_2]),
            ('GRID', (0, 0), (-1, -1), 0.5, grid_color),
            ('BOX', (0, 0), (-1, -1), 1, grid_color),
        ]))

        elements.append(t)
        doc.build(elements)


