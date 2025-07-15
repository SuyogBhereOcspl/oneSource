import os
import pandas as pd
from HR.models import DailyAttendance,AttendanceRegulation,DailyCheckIn,Late_Early_Go
from datetime import date, timedelta, time


# file_path = r'D:\ServerData\Attendance\Attendance_Regulation.xlsx'    ##for different location file keep is 
# pip install imapclient
# pip install pyzmail36     

# from imapclient import IMAPClient
# import pyzmail

# def fetch_and_download_attachment_imapclient():
#     USERNAME = 'suyog.b@ocspl.com'
#     PASSWORD = 'Suy098787'
#     IMAP_URL = 'imap-mail.outlook.com'

    # with IMAPClient(IMAP_URL) as client:
    #     client.login(USERNAME, PASSWORD)
    #     client.select_folder('INBOX', readonly=True)

    #     messages = client.search(['UNSEEN', 'sahil.c@ocspl.com', 'Notification for report Daily Attendance report'])
    #     for uid, message_data in client.fetch(messages, 'RFC822').items():
    #         message = pyzmail.PyzMessage.factory(message_data[b'RFC822'])
    #         for attachment in message.mailparts:
    #             if attachment.is_attachment:
    #                 file_path = os.path.join('attendance_uploads', attachment.filename)
    #                 with open(file_path, 'wb') as f:
                        # f.write(attachment.get_payload())
        #             print(f"Downloaded {attachment.filename} to attendance_uploads")

        # print("Email attachments fetched and downloaded.")
# # 
# Call the function to execute
# fetch_and_download_attachment_imapclient()

# def fetch_and_download_attachment():
#     print("[TASK STARTED] Fetching emails with attachments...")
#     USERNAME = 'suyog.b@ocspl.com'
#     PASSWORD = 'Suy098787'
#     IMAP_URL = 'imap.gmail.com'
#     SENDER = 'specific-sender@example.com'
#     SUBJECT = 'Notification for report Daily Attendance report'
#     ATTACHMENT_DIR = 'attendance_uploads'

#     mail = imaplib.IMAP4_SSL(IMAP_URL)
#     mail.login(USERNAME, PASSWORD)
#     mail.select('inbox')

#     # Search for unread emails from specific sender and with specific subject
#     status, messages = mail.search(None, '(UNSEEN)', f'(FROM "{SENDER}")', f'(SUBJECT "{SUBJECT}")')
#     messages = messages[0].split()

#     for msg_num in messages:
#         _, data = mail.fetch(msg_num, '(RFC822)')
#         for response_part in data:
#             if isinstance(response_part, tuple):
#                 message = email.message_from_bytes(response_part[1])
#                 for part in message.walk():
#                     if part.get_content_maintype() == 'multipart':
#                         continue
#                     if part.get('Content-Disposition') is None:
#                         continue

#                     filename = part.get_filename()
#                     if filename:
#                         filepath = os.path.join(ATTACHMENT_DIR, filename)
#                         if not os.path.exists(ATTACHMENT_DIR):
#                             os.makedirs(ATTACHMENT_DIR)
#                         with open(filepath, 'wb') as f:
#                             f.write(part.get_payload(decode=True))
#                         print(f"[DOWNLOADED] {filename} saved to {ATTACHMENT_DIR}")

#     mail.close()
#     mail.logout()
#     print("[SUCCESS] Email attachments fetched and downloaded.")





def upload_daily_attendance():
    print("[TASK STARTED] Uploading daily attendance...")
    file_path = os.path.join('attendance_uploads', 'Daily_Attendance.xlsx')

    if not os.path.exists(file_path):
        print(f"[ERROR] File not found: {file_path}")
        return

    df = pd.read_excel(file_path)

    fifty_days_ago = date.today() - timedelta(days=100)

    for _, row in df.iterrows():
        emp_code = str(row['Employee Code']).strip()

        attendance_date_raw = pd.to_datetime(row['Attendance date'], errors='coerce')

        # Skip if the attendance_date is NaT
        if pd.isna(attendance_date_raw):
            print(f"[SKIPPED] {emp_code} — missing or invalid attendance date")
            continue

        attendance_date = attendance_date_raw.date()

        if attendance_date < fifty_days_ago:
            print(f"[SKIPPED] {emp_code} on {attendance_date} — older than 50 days")
            continue
        status_in_out = row['Status']

        obj, created = DailyAttendance.objects.update_or_create(
            employee_code=emp_code,
            attendance_date=attendance_date,
            status_in_out=status_in_out,
            defaults={
                'full_name': row['Full name'],
                'employment_status': row['Employment status'],
                'company': row['Company'],
                'business_unit': row.get('Business Unit', None),
                'department': row['Department'],
                'designation': row.get('Designation', None),
                'branch': row['Branch'],
                'sub_branch': row['Sub branch'],
                'punch_in_punch_out_time': row.get('Punch/clocking time', None),
                'shift_code': row['Shift code'],
                'shift_timing': row['Shift timings'],
                'Late_or_early': row.get('Late or early', None),
                'working_hours': row.get('Working hour', None),
                'total_office_hours': row.get('Total office hours', None),
                'source': row.get('Source', None),
                'date_of_joining': pd.to_datetime(row.get('Date of joining'), errors='coerce').date() if pd.notna(row.get('Date of joining')) else None,
                'employment_type': row.get('Employment type', None),
                'grade': row.get('Grade', None),
                'lattitude_longitude': row.get('Lat long', None),
                'level': row.get('Level', None),
                'location': row.get('Location', None),
                'mobile': row.get('Mobile number', None),
                'region': row.get('Region', None),
                'reporting_manager': row.get('Reporting manager', None),
                'work_email': row.get('Work email', None),

            }
        )

        action = "Created" if created else "Updated"
        # print(f"[{action}] {emp_code} on {attendance_date}")
    print("[SUCCESS] Attendance data imported (within 50 days only).")






def upload_attendance_regulation():
    print("[TASK STARTED] Uploading attendance regulation...")
    file_path = os.path.join('attendance_uploads', 'AR_Request_2.xlsx')

    if not os.path.exists(file_path):
        print(f"[ERROR] File not found: {file_path}")
        return

    df = pd.read_excel(file_path)
    fifty_days_ago = date.today() - timedelta(days=50)

    for _, row in df.iterrows():
        try:
            emp_code = str(row['Employee Code']).strip()
            attendance_date = pd.to_datetime(row['Attendance date']).date()
            requested_on = pd.to_datetime(row['Request on'], errors='coerce').date() if pd.notna(row['Request on']) else None

            if attendance_date < fifty_days_ago:
                # print(f"[SKIPPED] {emp_code} on {attendance_date} — older than 50 days")
                continue

            obj, created = AttendanceRegulation.objects.update_or_create(
                employee_code=emp_code,
                attendance_date=attendance_date,
                requested_on=requested_on,
                defaults={
                    'full_name': row['Full name'],
                    'employment_status': row['Employment status'],
                    'company': row['Company'],
                    'business_unit': row['Business Unit'],
                    'department': row['Department'],
                    'designation': row['Designation'],
                    'branch': row['Branch'],
                    'sub_branch': row['Sub branch'],
                    'request_type': row['Request type'],
                    'attendance_day': row['Attendance day'],
                    'reason': row['Reason'],
                    'shift_code': row['Shift code'],
                    'shift_timings': row['Shift timings'],
                    'actual_punch_in_out': row.get('Actual punch in/ out', ''),
                    'punch_in_date': pd.to_datetime(row['Punch in (date)'], errors='coerce').date() if pd.notna(row['Punch in (date)']) else None,
                    'punch_in_time': row.get('Punch in timing', ''),
                    'punch_out_date': pd.to_datetime(row['Punch out (date)'], errors='coerce').date() if pd.notna(row['Punch out (date)']) else None,
                    'punch_out_time': row.get('Punch out timing', ''),
                    'remarks': row.get('Remarks', ''),
                    'request_status': row['Request status'],
                    'requested_by': row['Request by'],
                    'approved_by': row.get('Approved by', ''),
                    'approved_on': pd.to_datetime(row['Approved on'], errors='coerce').date() if pd.notna(row['Approved on']) else None,
                    'approver_remark': row.get('Approver remark', '')
                }
            )

            # print(f"[{'Created' if created else 'Updated'}] {emp_code} on {attendance_date}")

        except Exception as e:
            print(f"[ERROR] Failed to process row for {row.get('Employee Code')}: {e}")

    print("[SUCCESS] Attendance regulation data imported.")


def upload_daily_checkin():
    print("[TASK STARTED] Uploading daily check-in data...")
    file_path = os.path.join('attendance_uploads', 'TimeOffice_Daily_checkIn.xlsx')

    if not os.path.exists(file_path):
        print(f"[ERROR] File not found: {file_path}")
        return

    df = pd.read_excel(file_path)
    fifty_days_ago = date.today() - timedelta(days=50)

    for _, row in df.iterrows():
        try:
            emp_code = str(row['Employee Code']).strip()
            attendance_date = pd.to_datetime(row['Attendance date']).date()

            if attendance_date < fifty_days_ago:
                # Skipping records older than 50 days
                continue

            obj, created = DailyCheckIn.objects.update_or_create(
                employee_code=emp_code,
                attendance_date=attendance_date,
                defaults={
                    'full_name': row['Full name'],
                    'employment_status': row['Employment status'],
                    'company': row['Company'],
                    'business_unit': row['Business Unit'],
                    'department': row['Department'],
                    'designation': row['Designation'],
                    'branch': row['Branch'],
                    'sub_branch': row['Sub branch'],
                    'shift': row.get('Shift', ''),
                    'check_in': row.get('Check in', ''),
                    'first_punch': pd.to_datetime(row['First punch'], errors='coerce').time() if pd.notna(row['First punch']) else None,
                    'last_punch': pd.to_datetime(row['Last punch'], errors='coerce').time() if pd.notna(row['Last punch']) else None,
                    'raw_punch': row.get('Raw punch', '')
                }
            )
            print(f"[{'Created' if created else 'Updated'}] Record for {emp_code} on {attendance_date}")

        except Exception as e:
            print(f"[ERROR] Failed to process row for {emp_code}: {e}")

    print("[SUCCESS] Daily check-in data imported.")



def upload_late_early_go():
    print("[TASK STARTED] Uploading late and early go data...")
    file_path = os.path.join('attendance_uploads', 'Late_and_Early_go.xlsx')

    if not os.path.exists(file_path):
        print(f"[ERROR] File not found: {file_path}")
        return

    df = pd.read_excel(file_path)
    today = date.today()
    fifty_days_ago = today - timedelta(days=50)

    for _, row in df.iterrows():
        try:
            emp_code = str(row['Employee Code']).strip()
            attendance_date = pd.to_datetime(row['Attendance date']).date()

            # Skipping records older than 50 days
            if attendance_date < fifty_days_ago:
                continue

            # Update or create a new record in the database
            obj, created = Late_Early_Go.objects.update_or_create(
                employee_code=emp_code,
                attendance_date=attendance_date,
                defaults={
                    'full_name': row['Full name'],
                    'employment_status': row['Employment status'],
                    'company': row['Company'],
                    'business_unit': row['Business Unit'],
                    'department': row['Department'],
                    'designation': row['Designation'],
                    'branch': row['Branch'],
                    'sub_branch': row['Sub branch'],
                    'late_early': row['Late / early'],
                    'late_early_by_min': int(row['Late/early by (min)']),
                    'shift_code': row['Shift code'],
                    'shift_timings': row['Shift timings']
                }
            )
            print(f"[{'Created' if created else 'Updated'}] Record for {emp_code} on {attendance_date}")

        except Exception as e:
            print(f"[ERROR] Failed to process row for {emp_code}: {e}")

    print("[SUCCESS] Late and early go data imported.")


