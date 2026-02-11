from django.http import JsonResponse, HttpResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from django.conf import settings
import os
import json
import datetime
try:
    import importlib
    _decorators = importlib.import_module("rest_framework.decorators")
    api_view = _decorators.api_view
    permission_classes = _decorators.permission_classes
    _permissions = importlib.import_module("rest_framework.permissions")
    IsAuthenticated = _permissions.IsAuthenticated
except Exception:
    # lightweight no-op fallbacks for environments without DRF installed
    def api_view(methods):
        def decorator(func):
            return func
        return decorator

    def permission_classes(classes):
        def decorator(func):
            return func
        return decorator

    class IsAuthenticated:
        pass

# In-memory store for demo purposes (fallback)
_ENTRIES = []
_VISITORS = []
_FAULTS = []
_FIELD_ACTIVITIES = []

import os
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from gridapp.models import Staff, ServerRoomEntry, FaultReport, FieldActivity, FaultFeedback, ServerRoomVisitor


@csrf_exempt
def server_room(request):
    # allow simple CORS for local development
    if request.method == 'OPTIONS':
        resp = JsonResponse({'ok': True})
        resp['Access-Control-Allow-Origin'] = '*'
        resp['Access-Control-Allow-Methods'] = 'GET,POST,OPTIONS'
        resp['Access-Control-Allow-Headers'] = 'Content-Type'
        return resp
    if request.method == 'GET':
        out = []
        try:
            qs = ServerRoomEntry.objects.select_related('staff').all()
            out = [
                {
                    'id': e.id,
                    'staff': e.staff.name,
                    'date': str(e.date),
                    'time_in': e.time_in.isoformat(),
                    'time_out': e.time_out.isoformat() if e.time_out else None,
                    'reason': e.reason,
                    'equipment_touched': e.equipment_touched,
                    'supervisor': e.supervisor,
                }
                for e in qs
            ]
        except Exception:
            out = []

        # include any in-memory fallback entries so they are visible to the frontend
        if _ENTRIES:
            out = out + _ENTRIES

        resp = JsonResponse(out, safe=False)
        resp['Access-Control-Allow-Origin'] = '*'
        return resp

    if request.method == 'POST':
        try:
            payload = json.loads(request.body.decode('utf-8'))
        except Exception:
            return JsonResponse({'error': 'invalid json'}, status=400)

        required = ['staff', 'date', 'time_in', 'time_out', 'reason', 'equipment_touched', 'supervisor']
        for field in required:
            if field not in payload:
                return JsonResponse({'error': f'missing field {field}'}, status=400)

        staff_name = payload.get('staff')
        staff_obj = None
        if staff_name:
            try:
                staff_obj, _ = Staff.objects.get_or_create(name=staff_name)
            except Exception:
                staff_obj = None
        try:
            if staff_obj:
                date = datetime.date.fromisoformat(payload.get('date'))
                time_in = datetime.time.fromisoformat(payload.get('time_in'))
                time_out = datetime.time.fromisoformat(payload.get('time_out')) if payload.get('time_out') else None
                sre = ServerRoomEntry.objects.create(
                    staff=staff_obj,
                    date=date,
                    time_in=time_in,
                    time_out=time_out,
                    reason=payload.get('reason'),
                    equipment_touched=payload.get('equipment_touched'),
                    supervisor=payload.get('supervisor'),
                )
                resp = JsonResponse({'id': sre.id, 'staff': sre.staff.name, 'date': str(sre.date)}, status=201)
            else:
                entry = {
                    'id': len(_ENTRIES) + 1,
                    'staff': payload.get('staff'),
                    'date': payload.get('date'),
                    'time_in': payload.get('time_in'),
                    'time_out': payload.get('time_out'),
                    'reason': payload.get('reason'),
                    'equipment_touched': payload.get('equipment_touched'),
                    'supervisor': payload.get('supervisor'),
                }
                _ENTRIES.append(entry)
                resp = JsonResponse(entry, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

        resp['Access-Control-Allow-Origin'] = '*'
        return resp

    return JsonResponse({'error': 'method not allowed'}, status=405)


@csrf_exempt
def server_room_visitors(request):
    if request.method == 'OPTIONS':
        resp = JsonResponse({'ok': True})
        resp['Access-Control-Allow-Origin'] = '*'
        resp['Access-Control-Allow-Methods'] = 'GET,POST,OPTIONS'
        resp['Access-Control-Allow-Headers'] = 'Content-Type'
        return resp

    if request.method == 'GET':
        out = []
        try:
            qs = ServerRoomVisitor.objects.all()
            out = [
                {
                    'id': v.id,
                    'staff_id': v.staff_id,
                    'name': v.name,
                    'purpose': v.purpose,
                    'date': str(v.date),
                    'time_in': v.time_in.isoformat(),
                    'time_out': v.time_out.isoformat() if v.time_out else None,
                }
                for v in qs
            ]
        except Exception:
            out = []

        if _VISITORS:
            out = out + _VISITORS

        resp = JsonResponse(out, safe=False)
        resp['Access-Control-Allow-Origin'] = '*'
        return resp

    if request.method == 'POST':
        try:
            payload = json.loads(request.body.decode('utf-8'))
        except Exception:
            return JsonResponse({'error': 'invalid json'}, status=400)

        required = ['staff_id', 'name', 'purpose', 'time_in']
        for field in required:
            if field not in payload:
                return JsonResponse({'error': f'missing field {field}'}, status=400)

        try:
            date_str = payload.get('date')
            date_val = datetime.date.fromisoformat(date_str) if date_str else datetime.date.today()
            time_in = datetime.time.fromisoformat(payload.get('time_in'))
            time_out = datetime.time.fromisoformat(payload.get('time_out')) if payload.get('time_out') else None

            visit = ServerRoomVisitor.objects.create(
                staff_id=payload.get('staff_id'),
                name=payload.get('name'),
                purpose=payload.get('purpose'),
                date=date_val,
                time_in=time_in,
                time_out=time_out,
            )
            resp = JsonResponse(
                {
                    'id': visit.id,
                    'staff_id': visit.staff_id,
                    'name': visit.name,
                    'purpose': visit.purpose,
                    'date': str(visit.date),
                    'time_in': visit.time_in.isoformat(),
                    'time_out': visit.time_out.isoformat() if visit.time_out else None,
                },
                status=201,
            )
        except Exception as e:
            entry = {
                'id': len(_VISITORS) + 1,
                'staff_id': payload.get('staff_id'),
                'name': payload.get('name'),
                'purpose': payload.get('purpose'),
                'date': payload.get('date') or str(datetime.date.today()),
                'time_in': payload.get('time_in'),
                'time_out': payload.get('time_out'),
            }
            _VISITORS.append(entry)
            resp = JsonResponse(entry, status=201)

        resp['Access-Control-Allow-Origin'] = '*'
        return resp

    return JsonResponse({'error': 'method not allowed'}, status=405)


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def fault_detail(request, pk):
    """Retrieve or update a single FaultReport by id. PATCH accepts JSON with fields to update (e.g. status, resolution_remarks)."""
    try:
        f = FaultReport.objects.get(pk=pk)
    except FaultReport.DoesNotExist:
        return JsonResponse({'error': 'not found'}, status=404)

    if request.method == 'GET':
        item = {
            'id': f.id,
            'title': f.title,
            'description': f.description,
            'date_reported': str(f.date_reported),
            'reported_by': f.reported_by.name if f.reported_by else None,
            'assigned_to': f.assigned_to.name if f.assigned_to else None,
            'assigned_to_id': f.assigned_to.id if f.assigned_to else None,
            'location': f.location,
            'severity': f.severity,
            'status': f.status,
            'resolution_remarks': f.resolution_remarks,
        }
        if f.attachment:
            item['attachment_url'] = request.build_absolute_uri(f.attachment.url)
        return JsonResponse(item)

    # PATCH
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'error': 'invalid json'}, status=400)

    allowed = ['status', 'resolution_remarks', 'assigned_to']
    changed = False
    for k in allowed:
        if k in data:
            if k == 'assigned_to':
                # Handle staff assignment by ID or name
                assigned_value = data[k]
                if assigned_value:
                    assigned_staff = None
                    # Try to find by ID first if it's numeric
                    if isinstance(assigned_value, int) or (isinstance(assigned_value, str) and assigned_value.isdigit()):
                        try:
                            assigned_staff = Staff.objects.get(id=int(assigned_value))
                        except Staff.DoesNotExist:
                            pass
                    # If not found by ID, try by name
                    if not assigned_staff and isinstance(assigned_value, str):
                        try:
                            assigned_staff = Staff.objects.get(name__iexact=assigned_value)
                        except Staff.DoesNotExist:
                            pass
                    # If still not found, return error
                    if not assigned_staff:
                        return JsonResponse({'error': f'Staff "{assigned_value}" not found (search by name or id)'}, status=400)
                    f.assigned_to = assigned_staff
                    changed = True
                else:
                    f.assigned_to = None
                    changed = True
            else:
                setattr(f, k, data[k])
                changed = True

    if changed:
        try:
            f.save()
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'id': f.id, 'status': f.status, 'resolution_remarks': f.resolution_remarks, 'assigned_to': f.assigned_to.name if f.assigned_to else None})



@csrf_exempt
def fault_reports(request):
    # support CORS preflight
    if request.method == 'OPTIONS':
        resp = JsonResponse({'ok': True})
        resp['Access-Control-Allow-Origin'] = '*'
        resp['Access-Control-Allow-Methods'] = 'GET,POST,OPTIONS'
        resp['Access-Control-Allow-Headers'] = 'Content-Type'
        return resp

    if request.method == 'GET':
        out = []
        try:
            qs = FaultReport.objects.select_related('reported_by', 'assigned_to').all()
            out = []
            for f in qs:
                item = {
                    'id': f.id,
                    'title': f.title,
                    'description': f.description,
                    'date_reported': str(f.date_reported),
                    'reported_by': f.reported_by.name if f.reported_by else None,
                    'assigned_to': f.assigned_to.name if f.assigned_to else None,
                    'assigned_to_id': f.assigned_to.id if f.assigned_to else None,
                    'location': f.location,
                    'severity': f.severity,
                    'status': f.status,
                    'resolution_remarks': f.resolution_remarks,
                }
                if f.attachment:
                    item['attachment_url'] = request.build_absolute_uri(f.attachment.url)
                out.append(item)
        except Exception:
            out = []

        if _FAULTS:
            out = out + _FAULTS

        resp = JsonResponse(out, safe=False)
        resp['Access-Control-Allow-Origin'] = '*'
        return resp

    if request.method == 'POST':
        # accept multipart/form-data for file uploads
        data = request.POST
        file = request.FILES.get('attachment')

        required = ['title', 'description', 'date_reported', 'reported_by', 'location', 'severity', 'status']
        for field in required:
            if field not in data:
                return JsonResponse({'error': f'missing field {field}'}, status=400)

        try:
            reported_by_name = data.get('reported_by')
            reported_by_obj = None
            if reported_by_name:
                try:
                    reported_by_obj, _ = Staff.objects.get_or_create(name=reported_by_name)
                except Exception:
                    reported_by_obj = None
            fr = FaultReport.objects.create(
                title=data.get('title'),
                description=data.get('description'),
                date_reported=datetime.date.fromisoformat(data.get('date_reported')),
                reported_by=reported_by_obj,
                location=data.get('location'),
                severity=data.get('severity'),
                status=data.get('status'),
                resolution_remarks=data.get('resolution_remarks', ''),
            )
            if file:
                fr.attachment.save(file.name, file)
                fr.save()
            resp = JsonResponse({'id': fr.id, 'title': fr.title}, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

        resp['Access-Control-Allow-Origin'] = '*'
        return resp

    return JsonResponse({'error': 'method not allowed'}, status=405)



@csrf_exempt
def field_activities(request):
    # support basic CORS preflight
    if request.method == 'OPTIONS':
        resp = JsonResponse({'ok': True})
        resp['Access-Control-Allow-Origin'] = '*'
        resp['Access-Control-Allow-Methods'] = 'GET,POST,OPTIONS'
        resp['Access-Control-Allow-Headers'] = 'Content-Type'
        return resp

    if request.method == 'GET':
        out = []
        try:
            qs = FieldActivity.objects.select_related('staff').all()
            out = [
                {
                    'id': f.id,
                    'staff': f.staff.name,
                    'substation': f.substation,
                    'date': str(f.date),
                    'time_out': f.time_out.isoformat(),
                    'time_returned': f.time_returned.isoformat() if f.time_returned else None,
                    'purpose': f.purpose,
                    'work_done': f.work_done,
                    'materials_used': f.materials_used,
                    'supervisor_approval': f.supervisor_approval,
                }
                for f in qs
            ]
        except Exception:
            out = []

        if _FIELD_ACTIVITIES:
            out = out + _FIELD_ACTIVITIES

        resp = JsonResponse(out, safe=False)
        resp['Access-Control-Allow-Origin'] = '*'
        return resp

    if request.method == 'POST':
        try:
            payload = json.loads(request.body.decode('utf-8'))
        except Exception:
            return JsonResponse({'error': 'invalid json'}, status=400)

        required = ['staff', 'substation', 'date', 'time_out', 'time_returned', 'purpose', 'work_done', 'materials_used', 'supervisor_approval']
        for field in required:
            if field not in payload:
                return JsonResponse({'error': f'missing field {field}'}, status=400)

        staff_name = payload.get('staff')
        staff_obj = None
        if staff_name:
            try:
                staff_obj, _ = Staff.objects.get_or_create(name=staff_name)
            except Exception:
                staff_obj = None
        try:
            if staff_obj:
                fa = FieldActivity.objects.create(
                    staff=staff_obj,
                    substation=payload.get('substation'),
                    date=datetime.date.fromisoformat(payload.get('date')),
                    time_out=datetime.time.fromisoformat(payload.get('time_out')),
                    time_returned=datetime.time.fromisoformat(payload.get('time_returned')) if payload.get('time_returned') else None,
                    purpose=payload.get('purpose'),
                    work_done=payload.get('work_done'),
                    materials_used=payload.get('materials_used'),
                    supervisor_approval=payload.get('supervisor_approval'),
                )
                resp = JsonResponse({'id': fa.id, 'staff': fa.staff.name, 'substation': fa.substation}, status=201)
            else:
                entry = {
                    'id': len(_FIELD_ACTIVITIES) + 1,
                    'staff': payload.get('staff'),
                    'substation': payload.get('substation'),
                    'date': payload.get('date'),
                    'time_out': payload.get('time_out'),
                    'time_returned': payload.get('time_returned'),
                    'purpose': payload.get('purpose'),
                    'work_done': payload.get('work_done'),
                    'materials_used': payload.get('materials_used'),
                    'supervisor_approval': payload.get('supervisor_approval'),
                }
                _FIELD_ACTIVITIES.append(entry)
                resp = JsonResponse(entry, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

        resp['Access-Control-Allow-Origin'] = '*'
        return resp

    return JsonResponse({'error': 'method not allowed'}, status=405)


@csrf_exempt
def dashboard(request):
    # simple aggregated metrics and small trend arrays
    if request.method == 'OPTIONS':
        resp = JsonResponse({'ok': True})
        resp['Access-Control-Allow-Origin'] = '*'
        resp['Access-Control-Allow-Methods'] = 'GET,OPTIONS'
        resp['Access-Control-Allow-Headers'] = 'Content-Type'
        return resp

    if request.method != 'GET':
        return JsonResponse({'error': 'method not allowed'}, status=405)

    today = datetime.date.today().isoformat()

    try:
        server_room_entries_today = ServerRoomEntry.objects.filter(date=today).count()
    except Exception:
        server_room_entries_today = sum(1 for e in _ENTRIES if e.get('date') == today)

    try:
        field_activities_today = FieldActivity.objects.filter(date=today).count()
    except Exception:
        field_activities_today = sum(1 for f in _FIELD_ACTIVITIES if f.get('date') == today)

    try:
        active_faults = FaultReport.objects.exclude(status__in=['resolved', 'closed']).count()
    except Exception:
        active_faults = sum(1 for f in _FAULTS if f.get('status') not in ('resolved', 'closed'))

    try:
        total_staff_online_today = ServerRoomEntry.objects.filter(date=today).values('staff').distinct().count()
    except Exception:
        total_staff_online_today = len({e.get('staff') for e in _ENTRIES if e.get('date') == today})

    # simple 7-day trend for faults (counts per day)
    def date_range(days=7):
        base = datetime.date.today()
        return [(base - datetime.timedelta(days=i)).isoformat() for i in reversed(range(days))]

    faults_trend = []
    attendance_trend = []
    dates = date_range(7)
    for d in dates:
        try:
            faults_trend.append(FaultReport.objects.filter(date_reported=d).count())
        except Exception:
            faults_trend.append(sum(1 for f in _FAULTS if f.get('date_reported') == d))
        try:
            attendance_trend.append(ServerRoomEntry.objects.filter(date=d).values('staff').distinct().count())
        except Exception:
            attendance_trend.append(len({e.get('staff') for e in _ENTRIES if e.get('date') == d}))

    # most visited substations (from field activities)
    substation_counts = {}
    try:
        for fa in FieldActivity.objects.all():
            name = fa.substation
            if not name:
                continue
            substation_counts[name] = substation_counts.get(name, 0) + 1
    except Exception:
        for f in _FIELD_ACTIVITIES:
            name = f.get('substation')
            if not name:
                continue
            substation_counts[name] = substation_counts.get(name, 0) + 1
    most_visited = sorted(substation_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    data = {
        'total_staff_online_today': total_staff_online_today,
        'active_faults': active_faults,
        'server_room_entries_today': server_room_entries_today,
        'field_activities_today': field_activities_today,
        'faults_trend': faults_trend,
        'attendance_trend': attendance_trend,
        'most_visited_substations': [{'name': n, 'count': c} for n, c in most_visited],
        'dates': dates,
    }

    resp = JsonResponse(data, safe=False)
    resp['Access-Control-Allow-Origin'] = '*'
    return resp


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def daily_records(request):
    """Return all server-room entries, field activities, and faults for a given date.
    Accepts GET with optional `date=YYYY-MM-DD` query param (defaults to today).
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'method not allowed'}, status=405)

    qdate = request.GET.get('date')
    if not qdate:
        qdate = datetime.date.today().isoformat()

    # server room entries
    sre_out = []
    try:
        qs = ServerRoomEntry.objects.select_related('staff').filter(date=qdate)
        for e in qs:
            sre_out.append({
                'id': e.id,
                'staff': e.staff.name,
                'date': str(e.date),
                'time_in': e.time_in.isoformat(),
                'time_out': e.time_out.isoformat() if e.time_out else None,
                'reason': e.reason,
                'equipment_touched': e.equipment_touched,
                'supervisor': e.supervisor,
            })
    except Exception:
        sre_out = [e for e in _ENTRIES if e.get('date') == qdate]

    # field activities
    fa_out = []
    try:
        qs = FieldActivity.objects.select_related('staff').filter(date=qdate)
        for f in qs:
            fa_out.append({
                'id': f.id,
                'staff': f.staff.name,
                'substation': f.substation,
                'date': str(f.date),
                'time_out': f.time_out.isoformat(),
                'time_returned': f.time_returned.isoformat() if f.time_returned else None,
                'purpose': f.purpose,
                'work_done': f.work_done,
                'materials_used': f.materials_used,
                'supervisor_approval': f.supervisor_approval,
            })
    except Exception:
        fa_out = [f for f in _FIELD_ACTIVITIES if f.get('date') == qdate]

    # faults by reported date
    faults_out = []
    try:
        qs = FaultReport.objects.select_related('reported_by').filter(date_reported=qdate)
        for f in qs:
            item = {
                'id': f.id,
                'title': f.title,
                'description': f.description,
                'date_reported': str(f.date_reported),
                'reported_by': f.reported_by.name if f.reported_by else None,
                'location': f.location,
                'severity': f.severity,
                'status': f.status,
                'resolution_remarks': f.resolution_remarks,
            }
            if f.attachment:
                item['attachment_url'] = request.build_absolute_uri(f.attachment.url)
            faults_out.append(item)
    except Exception:
        faults_out = [f for f in _FAULTS if f.get('date_reported') == qdate]

    resp = JsonResponse({'date': qdate, 'server_room_entries': sre_out, 'field_activities': fa_out, 'faults': faults_out}, safe=False)
    resp['Access-Control-Allow-Origin'] = '*'
    return resp


def _csv_response(filename, fieldnames, rows):
    from django.http import HttpResponse
    import csv
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    writer = csv.DictWriter(response, fieldnames=fieldnames)
    writer.writeheader()
    for r in rows:
        writer.writerow(r)
    return response


def export_field_activities_csv(request):
    try:
        qs = FieldActivity.objects.select_related('staff').all()
        rows = []
        for f in qs:
            rows.append({
                'id': f.id,
                'staff': f.staff.name,
                'substation': f.substation,
                'date': str(f.date),
                'time_out': f.time_out.isoformat(),
                'time_returned': f.time_returned.isoformat() if f.time_returned else '',
                'purpose': f.purpose,
                'work_done': f.work_done,
                'materials_used': f.materials_used,
                'supervisor_approval': f.supervisor_approval,
            })
        fieldnames = ['id','staff','substation','date','time_out','time_returned','purpose','work_done','materials_used','supervisor_approval']
        return _csv_response('field_activities.csv', fieldnames, rows)
    except Exception:
        return JsonResponse({'error': 'could not export'}, status=500)


def export_activity_reports_weekly_csv(request):
    """Export field activities within a date range as CSV.
    Accepts optional `start` and `end` query params (YYYY-MM-DD). Defaults to last 7 days.
    """
    try:
        qstart = request.GET.get('start')
        qend = request.GET.get('end')
        today = datetime.date.today()
        if not qend:
            qend_date = today
        else:
            qend_date = datetime.date.fromisoformat(qend)
        if not qstart:
            qstart_date = qend_date - datetime.timedelta(days=6)
        else:
            qstart_date = datetime.date.fromisoformat(qstart)

        rows = []
        qs = FieldActivity.objects.select_related('staff').filter(date__gte=qstart_date, date__lte=qend_date)
        for f in qs:
            rows.append({
                'id': f.id,
                'staff': f.staff.name,
                'substation': f.substation,
                'date': str(f.date),
                'time_out': f.time_out.isoformat(),
                'time_returned': f.time_returned.isoformat() if f.time_returned else '',
                'purpose': f.purpose,
                'work_done': f.work_done,
                'materials_used': f.materials_used,
                'supervisor_approval': f.supervisor_approval,
            })
        fieldnames = ['id','staff','substation','date','time_out','time_returned','purpose','work_done','materials_used','supervisor_approval']
        return _csv_response(f'activity_reports_{qstart_date}_{qend_date}.csv', fieldnames, rows)
    except Exception:
        return JsonResponse({'error': 'could not export weekly activities'}, status=500)


def export_activity_reports_monthly_csv(request):
    """Export field activities for a calendar month as CSV.
    Accepts optional `month` (YYYY-MM) or `start` and `end` (YYYY-MM-DD).
    Defaults to the current calendar month (from day 1 to today).
    """
    try:
        qmonth = request.GET.get('month')
        qstart = request.GET.get('start')
        qend = request.GET.get('end')
        today = datetime.date.today()

        if qstart and qend:
            qstart_date = datetime.date.fromisoformat(qstart)
            qend_date = datetime.date.fromisoformat(qend)
        elif qmonth:
            # parse YYYY-MM
            year, mon = (int(x) for x in qmonth.split('-'))
            qstart_date = datetime.date(year, mon, 1)
            # last day of month: move to first of next month minus one day
            if mon == 12:
                qend_date = datetime.date(year + 1, 1, 1) - datetime.timedelta(days=1)
            else:
                qend_date = datetime.date(year, mon + 1, 1) - datetime.timedelta(days=1)
        else:
            # default to start of current month through today
            qstart_date = datetime.date(today.year, today.month, 1)
            qend_date = today

        rows = []
        qs = FieldActivity.objects.select_related('staff').filter(date__gte=qstart_date, date__lte=qend_date)
        for f in qs:
            rows.append({
                'id': f.id,
                'staff': f.staff.name,
                'substation': f.substation,
                'date': str(f.date),
                'time_out': f.time_out.isoformat(),
                'time_returned': f.time_returned.isoformat() if f.time_returned else '',
                'purpose': f.purpose,
                'work_done': f.work_done,
                'materials_used': f.materials_used,
                'supervisor_approval': f.supervisor_approval,
            })
        fieldnames = ['id','staff','substation','date','time_out','time_returned','purpose','work_done','materials_used','supervisor_approval']
        # filename uses YYYY-MM range for clarity
        return _csv_response(f'activity_reports_{qstart_date}_{qend_date}.csv', fieldnames, rows)
    except Exception:
        return JsonResponse({'error': 'could not export monthly activities'}, status=500)


def export_faults_csv(request):
    try:
        qs = FaultReport.objects.select_related('reported_by', 'assigned_to').all()
        rows = []
        for f in qs:
            rows.append({
                'id': f.id,
                'title': f.title,
                'description': f.description,
                'date_reported': str(f.date_reported),
                'reported_by': f.reported_by.name if f.reported_by else '',
                'assigned_to': f.assigned_to.name if f.assigned_to else '',
                'location': f.location,
                'severity': f.severity,
                'status': f.status,
                'resolution_remarks': f.resolution_remarks,
            })
        fieldnames = ['id','title','description','date_reported','reported_by','assigned_to','location','severity','status','resolution_remarks']
        return _csv_response('fault_reports.csv', fieldnames, rows)
    except Exception:
        return JsonResponse({'error': 'could not export'}, status=500)


@api_view(['GET'])
def export_daily_records_csv(request):
    try:
        # allow any authenticated user to export combined daily records
        qdate = request.GET.get('date') or datetime.date.today().isoformat()
        rows = []
        # server room entries
        try:
            qs = ServerRoomEntry.objects.select_related('staff').filter(date=qdate)
            for e in qs:
                rows.append({
                    'type': 'server_room',
                    'id': e.id,
                    'staff': e.staff.name,
                    'substation_or_location': '',
                    'date': str(e.date),
                    'time_in': e.time_in.isoformat(),
                    'time_out': e.time_out.isoformat() if e.time_out else '',
                    'title': '',
                    'description': e.reason,
                    'severity': '',
                    'status': '',
                    'resolution_remarks': '',
                })
        except Exception:
            for e in _ENTRIES:
                if e.get('date') == qdate:
                    rows.append({
                        'type': 'server_room',
                        'id': e.get('id'),
                        'staff': e.get('staff'),
                        'substation_or_location': '',
                        'date': e.get('date'),
                        'time_in': e.get('time_in'),
                        'time_out': e.get('time_out'),
                        'title': '',
                        'description': e.get('reason'),
                        'severity': '',
                        'status': '',
                        'resolution_remarks': '',
                    })

        # field activities
        try:
            qs = FieldActivity.objects.select_related('staff').filter(date=qdate)
            for f in qs:
                rows.append({
                    'type': 'field_activity',
                    'id': f.id,
                    'staff': f.staff.name,
                    'substation_or_location': f.substation,
                    'date': str(f.date),
                    'time_in': f.time_out.isoformat(),
                    'time_out': f.time_returned.isoformat() if f.time_returned else '',
                    'title': '',
                    'description': f.work_done,
                    'severity': '',
                    'status': '',
                    'resolution_remarks': '',
                })
        except Exception:
            for f in _FIELD_ACTIVITIES:
                if f.get('date') == qdate:
                    rows.append({
                        'type': 'field_activity',
                        'id': f.get('id'),
                        'staff': f.get('staff'),
                        'substation_or_location': f.get('substation'),
                        'date': f.get('date'),
                        'time_in': f.get('time_out'),
                        'time_out': f.get('time_returned'),
                        'title': '',
                        'description': f.get('work_done'),
                        'severity': '',
                        'status': '',
                        'resolution_remarks': '',
                    })

        # faults
        try:
            qs = FaultReport.objects.select_related('reported_by').filter(date_reported=qdate)
            for f in qs:
                rows.append({
                    'type': 'fault',
                    'id': f.id,
                    'staff': f.reported_by.name if f.reported_by else '',
                    'substation_or_location': f.location,
                    'date': str(f.date_reported),
                    'time_in': '',
                    'time_out': '',
                    'title': f.title,
                    'description': f.description,
                    'severity': f.severity,
                    'status': f.status,
                    'resolution_remarks': f.resolution_remarks,
                })
        except Exception:
            for f in _FAULTS:
                if f.get('date_reported') == qdate:
                    rows.append({
                        'type': 'fault',
                        'id': f.get('id'),
                        'staff': f.get('reported_by'),
                        'substation_or_location': f.get('location'),
                        'date': f.get('date_reported'),
                        'time_in': '',
                        'time_out': '',
                        'title': f.get('title'),
                        'description': f.get('description'),
                        'severity': f.get('severity'),
                        'status': f.get('status'),
                        'resolution_remarks': f.get('resolution_remarks'),
                    })

        fieldnames = ['type','id','staff','substation_or_location','date','time_in','time_out','title','description','severity','status','resolution_remarks']
        return _csv_response(f'daily_records_{qdate}.csv', fieldnames, rows)
    except Exception:
        return JsonResponse({'error': 'could not export daily records'}, status=500)


def activity_reports(request):
    # simple endpoint to return recent field activities or placeholder reports
    if request.method == 'OPTIONS':
        resp = JsonResponse({'ok': True})
        resp['Access-Control-Allow-Origin'] = '*'
        resp['Access-Control-Allow-Methods'] = 'GET,OPTIONS'
        resp['Access-Control-Allow-Headers'] = 'Content-Type'
        return resp

    if request.method != 'GET':
        return JsonResponse({'error': 'method not allowed'}, status=405)

    out = []
    try:
        qs = FieldActivity.objects.select_related('staff').order_by('-date')[:50]
        out = [
            {
                'id': f.id,
                'staff': f.staff.name,
                'substation': f.substation,
                'date': str(f.date),
                'time_out': f.time_out.isoformat(),
                'time_returned': f.time_returned.isoformat() if f.time_returned else None,
                'purpose': f.purpose,
                'work_done': f.work_done,
                'materials_used': f.materials_used,
                'supervisor_approval': f.supervisor_approval,
            }
            for f in qs
        ]
    except Exception:
        out = []

    # include any in-memory fallback field activities so they appear in reports
    if _FIELD_ACTIVITIES:
        for f in _FIELD_ACTIVITIES:
            out.append({
                'id': f.get('id'),
                'staff': f.get('staff'),
                'substation': f.get('substation'),
                'date': f.get('date'),
                'time_out': f.get('time_out'),
                'time_returned': f.get('time_returned'),
                'purpose': f.get('purpose'),
                'work_done': f.get('work_done'),
                'materials_used': f.get('materials_used'),
                'supervisor_approval': f.get('supervisor_approval'),
            })

    resp = JsonResponse(out, safe=False)
    resp['Access-Control-Allow-Origin'] = '*'
    return resp


@csrf_exempt
def fault_feedback(request):
    """Submit feedback for a resolved fault"""
    if request.method == 'OPTIONS':
        resp = JsonResponse({'ok': True})
        resp['Access-Control-Allow-Origin'] = '*'
        resp['Access-Control-Allow-Methods'] = 'POST,OPTIONS'
        resp['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return resp

    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
        except Exception:
            return JsonResponse({'error': 'invalid json'}, status=400)

        # Validate required fields
        fault_id = data.get('fault_id')
        staff_name = data.get('staff_name', '').strip()
        staff_email = data.get('staff_email', '').strip()
        feedback_text = data.get('feedback_text', '').strip()

        if not fault_id or not staff_name or not staff_email or not feedback_text:
            return JsonResponse({'error': 'missing required fields'}, status=400)

        try:
            fault = FaultReport.objects.get(id=fault_id)
        except FaultReport.DoesNotExist:
            return JsonResponse({'error': 'fault not found'}, status=404)

        try:
            feedback = FaultFeedback.objects.create(
                fault=fault,
                staff_name=staff_name,
                staff_email=staff_email,
                feedback_text=feedback_text
            )
            resp = JsonResponse({
                'id': feedback.id,
                'fault_id': fault.id,
                'staff_name': feedback.staff_name,
                'message': 'Feedback submitted successfully'
            }, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

        resp['Access-Control-Allow-Origin'] = '*'
        return resp

    return JsonResponse({'error': 'method not allowed'}, status=405)


@csrf_exempt
def get_fault_feedbacks(request, fault_id):
    """Get all feedbacks for a specific fault"""
    if request.method == 'OPTIONS':
        resp = JsonResponse({'ok': True})
        resp['Access-Control-Allow-Origin'] = '*'
        resp['Access-Control-Allow-Methods'] = 'GET,OPTIONS'
        resp['Access-Control-Allow-Headers'] = 'Content-Type'
        return resp

    if request.method == 'GET':
        try:
            feedbacks = FaultFeedback.objects.filter(fault_id=fault_id)
            out = []
            for fb in feedbacks:
                out.append({
                    'id': fb.id,
                    'staff_name': fb.staff_name,
                    'staff_email': fb.staff_email,
                    'feedback_text': fb.feedback_text,
                    'date_submitted': fb.date_submitted.isoformat()
                })
            resp = JsonResponse(out, safe=False)
            resp['Access-Control-Allow-Origin'] = '*'
            return resp
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'method not allowed'}, status=405)


def serve_index_html(request):
    """Serve index.html for React Router - enables client-side routing in production"""
    index_path = os.path.join(settings.STATIC_ROOT, 'index.html')
    
    # Try to serve index.html
    if os.path.exists(index_path):
        with open(index_path, 'r', encoding='utf-8') as f:
            return HttpResponse(f.read(), content_type='text/html')
    
    # Fallback: return a simple error message if index.html doesn't exist
    return HttpResponse(
        '<html><body><h1>404 - Frontend Not Built</h1>'
        '<p>Run: <code>cd ../frontend && npm run build</code></p></body></html>',
        content_type='text/html',
        status=404
    )
