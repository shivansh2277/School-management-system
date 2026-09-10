/**
 * GENERATED FILE — do not edit by hand.
 * Regenerate with `npm run api:types`. See docs/superpowers/specs/
 * 2026-09-08-web-erp-slice-0-foundation-design.md section 4.4.
 */
export interface paths {
    "/auth/login": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Login */
        post: operations["login_auth_login_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/auth/refresh": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Refresh */
        post: operations["refresh_auth_refresh_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/auth/me": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Me */
        get: operations["me_auth_me_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/auth/change-password": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Change Password */
        post: operations["change_password_auth_change_password_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/dashboard/stats": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Dashboard Stats */
        get: operations["dashboard_stats_admin_dashboard_stats_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/settings": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Settings */
        get: operations["get_settings_admin_settings_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Update Settings */
        patch: operations["update_settings_admin_settings_patch"];
        trace?: never;
    };
    "/admin/grade-bands": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Grade Bands */
        get: operations["grade_bands_admin_grade_bands_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/students": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Students */
        get: operations["list_students_admin_students_get"];
        put?: never;
        /** Create Student */
        post: operations["create_student_admin_students_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/students/export": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Export Students
         * @description Download the roster as CSV.
         *
         *     This route exists to make two controls real that until now gated nothing.
         *
         *     `students.profile.export` was granted to the Admin Officer and required by
         *     no route in `app/api/`, so the separation section 10.2 is proud of - being
         *     allowed to see a child on screen is not being allowed to download two
         *     thousand of them - was decorative. It is now the only way to get the file,
         *     and it is demanded school-wide so a guardian's own-children grant cannot
         *     reach it.
         *
         *     `AuditAction.export` had been in the enum since Part 1 and had never once
         *     been written. Every download is now a row in `audit_log` naming the actor,
         *     the filters and the count (section 5.10.9).
         *
         *     The rows come from `_roster()`, the same statement the screen uses, so this
         *     cannot become a way to see what the screen would not.
         *
         *     This is a GET that commits, which CLAUDE.md otherwise forbids. The rule
         *     exists to stop incidental writes on a read - v0's `refresh_overdue()`
         *     moving invoice statuses from inside a dashboard query. Here the write *is*
         *     the point: section 5.10.9 requires the download to be audited, and an audit
         *     row written only on some other request would not record the download. The
         *     exception is this route and the ones like it, not a licence generally.
         */
        get: operations["export_students_admin_students_export_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/students/{student_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Student Detail */
        get: operations["student_detail_admin_students__student_id__get"];
        put?: never;
        post?: never;
        /** Deactivate Student */
        delete: operations["deactivate_student_admin_students__student_id__delete"];
        options?: never;
        head?: never;
        /** Update Student */
        patch: operations["update_student_admin_students__student_id__patch"];
        trace?: never;
    };
    "/admin/teachers": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Teachers */
        get: operations["list_teachers_admin_teachers_get"];
        put?: never;
        /** Create Teacher */
        post: operations["create_teacher_admin_teachers_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/teachers/{teacher_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        /** Deactivate Teacher */
        delete: operations["deactivate_teacher_admin_teachers__teacher_id__delete"];
        options?: never;
        head?: never;
        /** Update Teacher */
        patch: operations["update_teacher_admin_teachers__teacher_id__patch"];
        trace?: never;
    };
    "/admin/classes": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Classes */
        get: operations["list_classes_admin_classes_get"];
        put?: never;
        /** Create Class */
        post: operations["create_class_admin_classes_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/classes/{class_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Update Class */
        patch: operations["update_class_admin_classes__class_id__patch"];
        trace?: never;
    };
    "/admin/classes/{class_id}/students": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Class Roster */
        get: operations["class_roster_admin_classes__class_id__students_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/subjects": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Subjects */
        get: operations["list_subjects_admin_subjects_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/timetable": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Timetable */
        get: operations["timetable_admin_timetable_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/exams": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Exams */
        get: operations["list_exams_admin_exams_get"];
        put?: never;
        /** Create Exam */
        post: operations["create_exam_admin_exams_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/exams/{exam_id}/schedule": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Exam Schedule */
        get: operations["exam_schedule_admin_exams__exam_id__schedule_get"];
        put?: never;
        /** Add Paper */
        post: operations["add_paper_admin_exams__exam_id__schedule_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/exams/papers/{exam_schedule_id}/lock": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Lock Paper
         * @description Close marks entry. After this a change needs an override and a reason.
         */
        post: operations["lock_paper_admin_exams_papers__exam_schedule_id__lock_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/exams/papers/{exam_schedule_id}/unlock": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Unlock Paper */
        post: operations["unlock_paper_admin_exams_papers__exam_schedule_id__unlock_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/exams/papers/{exam_schedule_id}/marks": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Paper Marks */
        get: operations["paper_marks_admin_exams_papers__exam_schedule_id__marks_get"];
        put?: never;
        /**
         * Enter Paper Marks
         * @description The exam controller's way in.
         *
         *     `/teacher/marks` reaches only the papers a teacher owns, which is right for
         *     a subject teacher and wrong for the person §5.4.8 puts in charge of
         *     moderation: an override on a locked paper is exactly the case where the
         *     actor does not teach the subject. The lock and the audit rules are the same
         *     either way — they live in the service, not in the route.
         *
         *     Gated on its own permission rather than on `exam.marks.enter`, because a
         *     teacher holds that one *unscoped* — the "own subjects only" restriction is
         *     enforced in the service, not by the grant. Reusing it here would have let
         *     any teacher mark any section in the school.
         */
        post: operations["enter_paper_marks_admin_exams_papers__exam_schedule_id__marks_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/grading-scales": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Scales */
        get: operations["list_scales_admin_grading_scales_get"];
        put?: never;
        /**
         * Create Scale
         * @description Create a scale, or the next version of one that already exists.
         *
         *     Reusing the name is how a school revises a frozen scale: the old version
         *     stays readable for the report cards that cite it.
         */
        post: operations["create_scale_admin_grading_scales_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/grading-scales/{scale_id}/bands": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        /** Replace Bands */
        put: operations["replace_bands_admin_grading_scales__scale_id__bands_put"];
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/grading-scales/{scale_id}/activate": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Activate */
        post: operations["activate_admin_grading_scales__scale_id__activate_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/assessment-schemes": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Schemes */
        get: operations["list_schemes_admin_assessment_schemes_get"];
        put?: never;
        /**
         * Create Scheme
         * @description Create a scheme. With no components given, the CBSE default is used —
         *     which is a pre-filled form, not an assumption the code makes elsewhere.
         */
        post: operations["create_scheme_admin_assessment_schemes_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/assessment-schemes/{scheme_id}/components": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        /** Replace Components */
        put: operations["replace_components_admin_assessment_schemes__scheme_id__components_put"];
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/assessment-schemes/{scheme_id}/activate": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Activate */
        post: operations["activate_admin_assessment_schemes__scheme_id__activate_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/report-cards/preview": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Preview
         * @description The live card. Moves when a mark is corrected — it is a screen.
         */
        get: operations["preview_admin_report_cards_preview_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/report-cards/readiness": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Readiness
         * @description What stands between this child and a published card.
         *
         *     Answered before publication is attempted rather than as a 409 afterwards:
         *     an exam controller working through a section wants the list, not a refusal
         *     per student.
         */
        get: operations["readiness_admin_report_cards_readiness_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/report-cards/publish": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Publish */
        post: operations["publish_admin_report_cards_publish_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/report-cards/{publication_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Issued
         * @description The card exactly as it was handed over. Never recomputed.
         */
        get: operations["issued_admin_report_cards__publication_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/report-cards": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Published */
        get: operations["list_published_admin_report_cards_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/report-cards/{publication_id}/release": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Release
         * @description Lift a withholding once the dues are cleared. The marks do not move.
         */
        post: operations["release_admin_report_cards__publication_id__release_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/departments": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Departments */
        get: operations["list_departments_admin_departments_get"];
        put?: never;
        /** Create Department */
        post: operations["create_department_admin_departments_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/departments/{department_id}/head": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        /** Set Head */
        put: operations["set_head_admin_departments__department_id__head_put"];
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/employees": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Employees */
        get: operations["list_employees_admin_employees_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/employees/{employee_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Employee */
        get: operations["employee_admin_employees__employee_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/employees/{employee_id}/assignment": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        /** Assign */
        put: operations["assign_admin_employees__employee_id__assignment_put"];
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/employees/{employee_id}/statutory": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Statutory
         * @description PAN, PF, ESI and bank. Its own permission, held by the principal and the
         *     auditor and nobody else who can merely read a staff record.
         */
        get: operations["statutory_admin_employees__employee_id__statutory_get"];
        /** Set Statutory */
        put: operations["set_statutory_admin_employees__employee_id__statutory_put"];
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/employees/{employee_id}/allocations": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Allocations
         * @description What would be left unattended if this person walked out today.
         *
         *     Answered before an exit is attempted rather than as a 409 afterwards: the
         *     office wants the list of what to reassign, not a refusal.
         */
        get: operations["allocations_admin_employees__employee_id__allocations_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/employees/{employee_id}/exit": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Record Exit */
        post: operations["record_exit_admin_employees__employee_id__exit_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/staff-leave/types": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Types */
        get: operations["list_types_admin_staff_leave_types_get"];
        put?: never;
        /** Create Type */
        post: operations["create_type_admin_staff_leave_types_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/staff-leave/balances/{employee_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Balances */
        get: operations["balances_admin_staff_leave_balances__employee_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/staff-leave": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Requests */
        get: operations["list_requests_admin_staff_leave_get"];
        put?: never;
        /** Apply */
        post: operations["apply_admin_staff_leave_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/staff-leave/{request_id}/affected-periods": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Affected
         * @description What this leave would leave uncovered, before it is approved.
         */
        get: operations["affected_admin_staff_leave__request_id__affected_periods_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/staff-leave/{request_id}/approve": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Approve */
        post: operations["approve_admin_staff_leave__request_id__approve_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/staff-leave/{request_id}/reject": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Reject */
        post: operations["reject_admin_staff_leave__request_id__reject_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/staff-leave/{request_id}/cancel": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Cancel */
        post: operations["cancel_admin_staff_leave__request_id__cancel_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/staff-attendance": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Roll
         * @description Everyone in service, marked or not — a register that lists only the
         *     people somebody remembered to mark is not a register.
         */
        get: operations["roll_admin_staff_attendance_get"];
        put?: never;
        /** Mark */
        post: operations["mark_admin_staff_attendance_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/staff-attendance/summary/{employee_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Summary
         * @description Working days, what was marked, and the loss-of-pay days payroll uses.
         */
        get: operations["summary_admin_staff_attendance_summary__employee_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/payroll/components": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Components
         * @description Every component, active or not — a school switching DA on needs to see
         *     the one that is off.
         */
        get: operations["components_admin_payroll_components_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/payroll/components/{component_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        /**
         * Update Component
         * @description Change a rate, or switch a component on or off.
         *
         *     This is §3.16's whole point: a school that pays HRA at 30% edits a number
         *     here rather than asking for a code change.
         */
        put: operations["update_component_admin_payroll_components__component_id__put"];
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/payroll/structures/{employee_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Structure */
        get: operations["structure_admin_payroll_structures__employee_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/payroll/structures": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Set Structure
         * @description Put somebody on new terms. Supersedes rather than edits.
         */
        post: operations["set_structure_admin_payroll_structures_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/payroll/preview/{employee_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Preview
         * @description What this person's payslip would say, without running anything.
         *
         *     Uses the same `compute()` the run does, so a preview and the real thing
         *     cannot drift.
         */
        get: operations["preview_admin_payroll_preview__employee_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/payroll/runs": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Runs */
        get: operations["list_runs_admin_payroll_runs_get"];
        put?: never;
        /** Open Run */
        post: operations["open_run_admin_payroll_runs_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/payroll/runs/{run_id}/calculate": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Calculate */
        post: operations["calculate_admin_payroll_runs__run_id__calculate_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/payroll/runs/{run_id}/approve": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Approve */
        post: operations["approve_admin_payroll_runs__run_id__approve_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/payroll/runs/{run_id}/paid": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Mark Paid */
        post: operations["mark_paid_admin_payroll_runs__run_id__paid_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/payroll/runs/{run_id}/discard": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Discard */
        post: operations["discard_admin_payroll_runs__run_id__discard_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/payroll/runs/{run_id}/payslips": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Payslips */
        get: operations["payslips_admin_payroll_runs__run_id__payslips_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/payroll/payslips/{payslip_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Payslip */
        get: operations["payslip_admin_payroll_payslips__payslip_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/payroll/runs/{run_id}/register/{code}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Register
         * @description A statutory register — PF, ESI, TDS (§5.3.10).
         */
        get: operations["register_admin_payroll_runs__run_id__register__code__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/payroll/runs/{run_id}/cost-by-department": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Cost By Department */
        get: operations["cost_by_department_admin_payroll_runs__run_id__cost_by_department_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/notices": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Notices */
        get: operations["list_notices_admin_notices_get"];
        put?: never;
        /** Publish */
        post: operations["publish_admin_notices_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/notices/{notice_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        /** Delete */
        delete: operations["delete_admin_notices__notice_id__delete"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/comms/preview": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Preview
         * @description Who this would reach, before anybody sends it (§5.9.9).
         *
         *     Also the honest half: `unreachable` counts the families with no address on
         *     file. A circular that reaches two thirds of the school should say so at the
         *     moment it is still a draft.
         */
        post: operations["preview_admin_comms_preview_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/comms/messages": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Messages */
        get: operations["messages_admin_comms_messages_get"];
        put?: never;
        /** Compose */
        post: operations["compose_admin_comms_messages_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/comms/messages/{message_id}/approve": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Approve */
        post: operations["approve_admin_comms_messages__message_id__approve_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/comms/broadcast": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Broadcast
         * @description The emergency broadcast of §5.9.3, deliberately its own thing.
         *
         *     It bypasses every opt-out and the quiet hours, and it skips the bulk
         *     approval — "the school is closed tomorrow" cannot wait for a second
         *     signature at nine at night, which is the situation the whole feature is
         *     for. It is audited like everything else, and §5.9.10 asks for that audit
         *     trail specifically.
         */
        post: operations["broadcast_admin_comms_broadcast_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/comms/messages/{message_id}/cancel": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Cancel */
        post: operations["cancel_admin_comms_messages__message_id__cancel_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/comms/messages/{message_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Delivery Report
         * @description The per-campaign delivery report of §5.9.10.
         */
        get: operations["delivery_report_admin_comms_messages__message_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/comms/unreachable": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Unreachable
         * @description Families with no email on file (§5.9.10).
         *
         *     §0.11 made email the only v1 channel, so this is the list that says how
         *     much of the school a circular cannot reach — and the phone number the
         *     office will have to ring instead.
         */
        get: operations["unreachable_admin_comms_unreachable_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/comms/templates": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Templates */
        get: operations["templates_admin_comms_templates_get"];
        put?: never;
        /**
         * Supersede Template
         * @description Add a version. Never an edit in place (§5.9.9).
         *
         *     The wording a school uses is theirs to change without a deploy (§0.18), and
         *     changing it must not rewrite what was sent last term.
         */
        post: operations["supersede_template_admin_comms_templates_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/comms/preferences": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        /**
         * Set Preference
         * @description A person's own opt-out, set by that person.
         *
         *     Gated on a permission everybody holds, because this changes nothing but the
         *     caller's own preferences — and recorded even for a category that overrides
         *     it, so the choice is on file the day that changes.
         */
        put: operations["set_preference_admin_comms_preferences_put"];
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/fees/invoices": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Invoices */
        get: operations["invoices_admin_fees_invoices_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/fees/invoices/generate": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Generate */
        post: operations["generate_admin_fees_invoices_generate_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/fees/invoices/{invoice_id}/void": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Void Invoice */
        post: operations["void_invoice_admin_fees_invoices__invoice_id__void_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/fees/ledger/{student_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Ledger */
        get: operations["ledger_admin_fees_ledger__student_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/fees/payments": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Collect */
        post: operations["collect_admin_fees_payments_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/fees/payments/{payment_id}/reverse": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Reverse */
        post: operations["reverse_admin_fees_payments__payment_id__reverse_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/fees/defaulters": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Defaulters
         * @description Who owes what, worst first, with a phone number to ring (§5.5.3).
         *
         *     Thin, like the rest of this router. The list itself moved into
         *     `services/fees.py` when the defaulter chase in Communication needed the
         *     same one — two queries would drift, and §5.10.9 names that as the way a
         *     number stops meaning anything.
         */
        get: operations["defaulters_admin_fees_defaulters_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/fees/daybook": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Daybook
         * @description The day's collection register, by mode and by cashier (§5.5.10).
         */
        get: operations["daybook_admin_fees_daybook_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/fees/periods": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Periods */
        get: operations["periods_admin_fees_periods_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/fees/periods/{year}/{month}/close": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Close Period */
        post: operations["close_period_admin_fees_periods__year___month__close_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/fees/periods/{year}/{month}/reopen": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Reopen Period */
        post: operations["reopen_period_admin_fees_periods__year___month__reopen_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/fees/collection": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Collection */
        get: operations["collection_admin_fees_collection_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/fees/heads": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Heads */
        get: operations["heads_admin_fees_heads_get"];
        put?: never;
        /** Create Head */
        post: operations["create_head_admin_fees_heads_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/fees/plans": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Plans */
        get: operations["plans_admin_fees_plans_get"];
        put?: never;
        /** Create Plan */
        post: operations["create_plan_admin_fees_plans_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/fees/assignments": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Assign Plan */
        post: operations["assign_plan_admin_fees_assignments_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/fees/concessions": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Concessions */
        get: operations["concessions_admin_fees_concessions_get"];
        put?: never;
        /** Request Concession */
        post: operations["request_concession_admin_fees_concessions_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/fees/concessions/{concession_id}/decide": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Decide Concession */
        post: operations["decide_concession_admin_fees_concessions__concession_id__decide_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/fees/concessions/sibling-sweep": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Sibling Sweep
         * @description Grant the §0.6 sibling concession to every family that qualifies.
         *
         *     Idempotent, so it is safe to run after any admission intake rather than
         *     remembering which families are new.
         */
        post: operations["sibling_sweep_admin_fees_concessions_sibling_sweep_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/attendance": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Attendance Roll
         * @description Read-only: admins do not mark attendance (BLUEPRINT §9 matrix).
         *
         *     Moved here from `api/admin/exams.py`, where it was declared on the exams
         *     router and so gated on `exam.definition.read` instead of
         *     `attendance.record.read`. That let the Exam Controller (who holds the exam
         *     permission but not the attendance one) read the roll while the `/attendance`
         *     web screen — gated on `attendance.record.read` per `web/src/screens.ts` —
         *     stayed hidden from them, and let anyone holding `attendance.record.read`
         *     alone open that screen and get a 403 from both of its fetches. The route
         *     now lives on the router whose permission it actually needs.
         */
        get: operations["attendance_roll_admin_attendance_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/attendance/summary": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Attendance Summary
         * @description See `attendance_roll` above for why this moved out of `exams.py`.
         */
        get: operations["attendance_summary_admin_attendance_summary_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/attendance/absentees": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Absentees */
        get: operations["absentees_admin_attendance_absentees_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/attendance/shortage": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Shortage
         * @description Children below the attendance threshold.
         *
         *     `threshold` now defaults to the school's setting rather than to 75.0 in the
         *     signature. What counts as short attendance is a policy - CBSE's 75% is the
         *     common answer and not the only one - and every other policy number here
         *     lives in `core/settings_registry.py` (CLAUDE.md: money rules are settings,
         *     not constants).
         */
        get: operations["shortage_admin_attendance_shortage_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/attendance/holidays": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Holidays */
        get: operations["holidays_admin_attendance_holidays_get"];
        put?: never;
        /** Add Holiday */
        post: operations["add_holiday_admin_attendance_holidays_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/attendance/leave-requests": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Leave Requests */
        get: operations["leave_requests_admin_attendance_leave_requests_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/attendance/leave-requests/{request_id}/decide": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Decide */
        post: operations["decide_admin_attendance_leave_requests__request_id__decide_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/timetable/periods": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Periods */
        get: operations["periods_admin_timetable_periods_get"];
        put?: never;
        /** Add Period */
        post: operations["add_period_admin_timetable_periods_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/timetable/slots": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Slots */
        get: operations["slots_admin_timetable_slots_get"];
        put?: never;
        /** Create Slot */
        post: operations["create_slot_admin_timetable_slots_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/timetable/slots/check": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Check
         * @description What would go wrong if this lesson were placed here.
         *
         *     A separate read so a builder can colour a cell while the coordinator drags
         *     it, without writing anything (§5.7.9 wants live validation, not a
         *     validate-at-the-end button).
         */
        post: operations["check_admin_timetable_slots_check_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/timetable/slots/{slot_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        /** Update Slot */
        put: operations["update_slot_admin_timetable_slots__slot_id__put"];
        post?: never;
        /** Delete Slot */
        delete: operations["delete_slot_admin_timetable_slots__slot_id__delete"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/timetable/workload": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Workload */
        get: operations["workload_admin_timetable_workload_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/timetable/completeness": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Completeness */
        get: operations["completeness_admin_timetable_completeness_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/timetable/day": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Day Plan
         * @description The day as it will actually run, substitutions applied.
         */
        get: operations["day_plan_admin_timetable_day_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/timetable/slots/{slot_id}/free-teachers": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Free Teachers */
        get: operations["free_teachers_admin_timetable_slots__slot_id__free_teachers_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/timetable/substitutions": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Substitutions */
        get: operations["substitutions_admin_timetable_substitutions_get"];
        put?: never;
        /** Arrange */
        post: operations["arrange_admin_timetable_substitutions_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/transport/vehicles": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Vehicles */
        get: operations["vehicles_admin_transport_vehicles_get"];
        put?: never;
        /** Add Vehicle */
        post: operations["add_vehicle_admin_transport_vehicles_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/transport/vehicles/{vehicle_id}/compliance": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Vehicle Compliance
         * @description What is missing before this bus may run. Empty `gaps` is roadworthy.
         */
        get: operations["vehicle_compliance_admin_transport_vehicles__vehicle_id__compliance_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/transport/vehicles/{vehicle_id}/status": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /**
         * Vehicle Status
         * @description Ground a bus, send it for service, or retire it.
         *
         *     Audited with a reason like any other status change. It does not cascade:
         *     the routes it is on stay as they are and simply stop being roadworthy,
         *     which is what makes the refusal visible rather than silently rewriting a
         *     school's timetable at 6am.
         */
        patch: operations["vehicle_status_admin_transport_vehicles__vehicle_id__status_patch"];
        trace?: never;
    };
    "/admin/transport/slabs": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Slabs */
        get: operations["slabs_admin_transport_slabs_get"];
        put?: never;
        /** Add Slab */
        post: operations["add_slab_admin_transport_slabs_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/transport/routes": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Routes */
        get: operations["routes_admin_transport_routes_get"];
        put?: never;
        /** Add Route */
        post: operations["add_route_admin_transport_routes_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/transport/routes/{route_id}/stops": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        /** Put Stops */
        put: operations["put_stops_admin_transport_routes__route_id__stops_put"];
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/transport/routes/{route_id}/crew": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Crew */
        patch: operations["crew_admin_transport_routes__route_id__crew_patch"];
        trace?: never;
    };
    "/admin/transport/routes/{route_id}/status": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Route Status */
        patch: operations["route_status_admin_transport_routes__route_id__status_patch"];
        trace?: never;
    };
    "/admin/transport/routes/{route_id}/roadworthiness": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Roadworthiness
         * @description Every reason this route may not carry children, in one call.
         *
         *     A read, so it reports rather than refuses — the setup screen shows all four
         *     expired papers at once instead of surfacing them one failed save at a time.
         */
        get: operations["roadworthiness_admin_transport_routes__route_id__roadworthiness_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/transport/routes/{route_id}/students": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Route Students
         * @description The list a driver actually needs (§5.6.10): who is at which stop, in the
         *     order the bus reaches them.
         */
        get: operations["route_students_admin_transport_routes__route_id__students_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/transport/assignments": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Assign */
        post: operations["assign_admin_transport_assignments_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/transport/assignments/{assignment_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Assignment Status */
        patch: operations["assignment_status_admin_transport_assignments__assignment_id__patch"];
        trace?: never;
    };
    "/admin/transport/charges": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Charges
         * @description What the bus will add to next month's invoices, before it is billed.
         *
         *     The same function the fee run calls, not a second one that computes it
         *     differently — reconciliation is the rule §5.10.9 is most insistent about.
         */
        get: operations["charges_admin_transport_charges_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/transport/requests": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Requests
         * @description Families who asked for the bus on their admission form and have no seat.
         *
         *     `transport_required` has been on every application since Part 2 and read by
         *     nothing. It seeds this queue rather than an assignment: the form says a
         *     family wants transport, never which stop, and choosing one for them off a
         *     postal address would be a guess about a child's walk to the bus.
         */
        get: operations["requests_admin_transport_requests_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/transport/expiring": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Expiring
         * @description The compliance dashboard of §5.6.10, already-lapsed papers included: a
         *     permit that expired last week is more urgent than one expiring next month,
         *     not less.
         */
        get: operations["expiring_admin_transport_expiring_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/configuration": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Read Settings
         * @description Values plus the vocabulary, so the screen can render controls it was not
         *     written against — the point of a registry.
         */
        get: operations["read_settings_admin_configuration_get"];
        /** Write Settings */
        put: operations["write_settings_admin_configuration_put"];
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/custom-fields": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Custom Fields */
        get: operations["list_custom_fields_admin_custom_fields_get"];
        put?: never;
        /** Create Custom Field */
        post: operations["create_custom_field_admin_custom_fields_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/custom-fields/{field_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        /**
         * Retire Custom Field
         * @description Retires the definition. Values already recorded are kept.
         */
        delete: operations["retire_custom_field_admin_custom_fields__field_id__delete"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/admission/cycles": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Cycles */
        get: operations["list_cycles_admin_admission_cycles_get"];
        put?: never;
        /** Create Cycle */
        post: operations["create_cycle_admin_admission_cycles_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/admission/cycles/{cycle_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Update Cycle */
        patch: operations["update_cycle_admin_admission_cycles__cycle_id__patch"];
        trace?: never;
    };
    "/admin/admission/cycles/{cycle_id}/classes": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Class Config */
        get: operations["list_class_config_admin_admission_cycles__cycle_id__classes_get"];
        /**
         * Set Class Config
         * @description Upsert: seat counts get revised repeatedly during a cycle, and a school
         *     should not have to know whether this class was configured already.
         */
        put: operations["set_class_config_admin_admission_cycles__cycle_id__classes_put"];
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/admission/enquiries": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Enquiries */
        get: operations["list_enquiries_admin_admission_enquiries_get"];
        put?: never;
        /** Create Enquiry */
        post: operations["create_enquiry_admin_admission_enquiries_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/admission/enquiries/{enquiry_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Enquiry Detail */
        get: operations["enquiry_detail_admin_admission_enquiries__enquiry_id__get"];
        put?: never;
        post?: never;
        /**
         * Mark Invalid
         * @description Enquiries are closed as invalid, never deleted: a wrong number is still
         *     a data point about where the enquiries are coming from.
         */
        delete: operations["mark_invalid_admin_admission_enquiries__enquiry_id__delete"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/admission/enquiries/{enquiry_id}/interactions": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Log Interaction */
        post: operations["log_interaction_admin_admission_enquiries__enquiry_id__interactions_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/admission/cycles/{cycle_id}/funnel": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Funnel */
        get: operations["funnel_admin_admission_cycles__cycle_id__funnel_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/admission/applications": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Applications */
        get: operations["list_applications_admin_admission_applications_get"];
        put?: never;
        /**
         * Create Application
         * @description Opens a draft. Nothing is validated against seats or age yet — a draft
         *     that refuses to save is a draft staff will keep on paper.
         */
        post: operations["create_application_admin_admission_applications_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/admission/applications/{application_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Application Detail */
        get: operations["application_detail_admin_admission_applications__application_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Update Application */
        patch: operations["update_application_admin_admission_applications__application_id__patch"];
        trace?: never;
    };
    "/admin/admission/applications/{application_id}/guardians": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        /**
         * Set Guardians
         * @description Replaces the whole set: step 3 is one form, edited as a whole, and
         *     reconciling a partial list is how a duplicate father appears.
         */
        put: operations["set_guardians_admin_admission_applications__application_id__guardians_put"];
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/admission/applications/{application_id}/siblings": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        /** Set Siblings */
        put: operations["set_siblings_admin_admission_applications__application_id__siblings_put"];
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/admission/sibling-search": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Sibling Search
         * @description Step 4 searches real students rather than accepting a typed name: the
         *     link is what triggers the sibling concession later.
         */
        get: operations["sibling_search_admin_admission_sibling_search_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/admission/applications/{application_id}/medical": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Read Medical */
        get: operations["read_medical_admin_admission_applications__application_id__medical_get"];
        /** Set Medical */
        put: operations["set_medical_admin_admission_applications__application_id__medical_put"];
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/admission/applications/{application_id}/submit": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Submit Application
         * @description Returns warnings rather than refusing on them: an out-of-range age or a
         *     possible duplicate is for a human to weigh (§5.1.9(1), (2)).
         */
        post: operations["submit_application_admin_admission_applications__application_id__submit_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/admission/applications/{application_id}/status": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Move Status */
        post: operations["move_status_admin_admission_applications__application_id__status_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/admission/applications/{application_id}/verify-claims": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Verify Claims
         * @description Re-check the sibling and staff-ward claims. An unverified claim never
         *     counts at selection time (§5.1.9(6)).
         */
        post: operations["verify_claims_admin_admission_applications__application_id__verify_claims_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/admission/applications/{application_id}/documents": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Checklist */
        get: operations["checklist_admin_admission_applications__application_id__documents_get"];
        put?: never;
        /** Upload Document */
        post: operations["upload_document_admin_admission_applications__application_id__documents_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/admission/documents/{document_id}/url": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Download Url
         * @description A link that expires in five minutes, minted per request. A permanent one
         *     that leaked would expose a child's birth certificate indefinitely.
         */
        get: operations["download_url_admin_admission_documents__document_id__url_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/admission/documents/{document_id}/verify": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Verify Document */
        post: operations["verify_document_admin_admission_documents__document_id__verify_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/admission/applications/{application_id}/assessments": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Schedule Assessment */
        post: operations["schedule_assessment_admin_admission_applications__application_id__assessments_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/admission/assessments": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Assessment Slot
         * @description The roster an assessor marks from.
         */
        get: operations["assessment_slot_admin_admission_assessments_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/admission/assessments/{assessment_id}/marks": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Record Marks */
        post: operations["record_marks_admin_admission_assessments__assessment_id__marks_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/admission/applications/{application_id}/interviews": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Schedule Interview */
        post: operations["schedule_interview_admin_admission_applications__application_id__interviews_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/admission/interviews/{interview_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Read Interview */
        get: operations["read_interview_admin_admission_interviews__interview_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/admission/interviews/{interview_id}/feedback": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Record Feedback */
        post: operations["record_feedback_admin_admission_interviews__interview_id__feedback_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/admission/applications/{application_id}/evaluation": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Evaluation
         * @description Everything scored about one applicant, for the 360° view.
         */
        get: operations["evaluation_admin_admission_applications__application_id__evaluation_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/admission/cycles/{cycle_id}/seats": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Seats
         * @description Filled against capacity per class — the top half of screen 1.
         */
        get: operations["seats_admin_admission_cycles__cycle_id__seats_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/admission/cycles/{cycle_id}/merit": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Merit
         * @description Screen 12. Decisions are made against a ranked class, not one
         *     application at a time (§5.1.2(5)).
         */
        get: operations["merit_admin_admission_cycles__cycle_id__merit_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/admission/applications/{application_id}/decision": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Decide */
        post: operations["decide_admin_admission_applications__application_id__decision_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/admission/cycles/{cycle_id}/decisions": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Decide Batch
         * @description A batch from the merit view. Each row still carries its own reason —
         *     "top 40 by merit" is a reason, and it is recorded against every one of the
         *     forty.
         */
        post: operations["decide_batch_admin_admission_cycles__cycle_id__decisions_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/admission/applications/{application_id}/offer": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Issue Offer */
        post: operations["issue_offer_admin_admission_applications__application_id__offer_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/admission/applications/{application_id}/offer/response": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Respond
         * @description Recorded by the office when the family answers. Declining releases the
         *     seat immediately and offers it to the next in the queue.
         */
        post: operations["respond_admin_admission_applications__application_id__offer_response_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/admission/cycles/{cycle_id}/waitlist": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Waitlist */
        get: operations["waitlist_admin_admission_cycles__cycle_id__waitlist_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/admission/cycles/{cycle_id}/waitlist/promote": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Promote
         * @description Manual promotion, for the school that would rather confirm each one
         *     than have the job do it.
         */
        post: operations["promote_admin_admission_cycles__cycle_id__waitlist_promote_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/admission/applications/{application_id}/decisions": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Decision History
         * @description Append-only: a reversal is a new row, so this is the whole story.
         */
        get: operations["decision_history_admin_admission_applications__application_id__decisions_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/admission/applications/{application_id}/payments": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Payments */
        get: operations["list_payments_admin_admission_applications__application_id__payments_get"];
        put?: never;
        /**
         * Collect Payment
         * @description Offline collection only — §0.10 defers the gateway to V2 — so what is
         *     recorded is cash, a cheque or a UPI reference somebody actually saw.
         */
        post: operations["collect_payment_admin_admission_applications__application_id__payments_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/admission/payments/{payment_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        /** Void Payment */
        delete: operations["void_payment_admin_admission_payments__payment_id__delete"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/admission/applications/{application_id}/conversion-preview": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Conversion Preview
         * @description Everything conversion would do, writing nothing (§5.1.9(18)).
         */
        get: operations["conversion_preview_admin_admission_applications__application_id__conversion_preview_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/admission/applications/{application_id}/convert": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Convert
         * @description One transaction: student, login, enrolment, guardians, links and
         *     documents (§5.1.9(16)). A partial conversion is the failure this exists to
         *     make impossible.
         */
        post: operations["convert_admin_admission_applications__application_id__convert_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/admission/cycles/{cycle_id}/dashboard": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Dashboard */
        get: operations["dashboard_admin_admission_cycles__cycle_id__dashboard_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/admission/cycles/{cycle_id}/reports": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Reports
         * @description §5.1.10, computed on read. A stored funnel disagrees with the register
         *     the first time somebody corrects a status.
         */
        get: operations["reports_admin_admission_cycles__cycle_id__reports_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/reports": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Library
         * @description The Report Library of section 5.10.3, by category.
         */
        get: operations["library_admin_reports_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/reports/{code}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Run
         * @description Run one report. Permission and scope are `reports._authorise()`.
         */
        get: operations["run_admin_reports__code__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/admin/reports/{code}/export": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Export
         * @description The same report as a CSV, audited.
         *
         *     The download runs the identical `svc.run()` the screen does - not a second
         *     query built for the file - so the two cannot show different rows. Section
         *     5.10.9's audit applies to every export, not only the student roster: a
         *     defaulter list is a list of families and what they owe, which is personal
         *     data by any reading.
         *
         *     A GET that commits, deliberately, for the reason given on the student
         *     export: the audit row is the requirement, not a side effect of a read.
         */
        get: operations["export_admin_reports__code__export_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/teacher/dashboard": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Dashboard */
        get: operations["dashboard_teacher_dashboard_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/teacher/classes": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** My Classes */
        get: operations["my_classes_teacher_classes_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/teacher/classes/{class_section_id}/students": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Class Roster */
        get: operations["class_roster_teacher_classes__class_section_id__students_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/teacher/timetable": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** My Timetable */
        get: operations["my_timetable_teacher_timetable_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/teacher/profile": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** My Profile */
        get: operations["my_profile_teacher_profile_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/teacher/subjects": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * My Subjects
         * @description Subjects this teacher owns, optionally within one section.
         */
        get: operations["my_subjects_teacher_subjects_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/teacher/attendance": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Roll Sheet */
        get: operations["roll_sheet_teacher_attendance_get"];
        put?: never;
        /** Mark */
        post: operations["mark_teacher_attendance_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/teacher/homework": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Homework */
        get: operations["list_homework_teacher_homework_get"];
        put?: never;
        /** Create */
        post: operations["create_teacher_homework_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/teacher/homework/{homework_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        /** Delete */
        delete: operations["delete_teacher_homework__homework_id__delete"];
        options?: never;
        head?: never;
        /** Update */
        patch: operations["update_teacher_homework__homework_id__patch"];
        trace?: never;
    };
    "/teacher/homework/{homework_id}/submissions": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Submissions */
        get: operations["submissions_teacher_homework__homework_id__submissions_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/teacher/exams": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * My Papers
         * @description Papers for the (section, subject) pairs this teacher owns.
         */
        get: operations["my_papers_teacher_exams_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/teacher/marks": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Roster */
        get: operations["roster_teacher_marks_get"];
        put?: never;
        /** Enter */
        post: operations["enter_teacher_marks_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/teacher/announcements": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Mine */
        get: operations["mine_teacher_announcements_get"];
        put?: never;
        /** Publish */
        post: operations["publish_teacher_announcements_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/student/dashboard": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Dashboard */
        get: operations["dashboard_student_dashboard_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/student/timetable": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Timetable */
        get: operations["timetable_student_timetable_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/student/profile": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Profile */
        get: operations["profile_student_profile_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/student/notices": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** My Notices */
        get: operations["my_notices_student_notices_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/student/attendance": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** My Attendance */
        get: operations["my_attendance_student_attendance_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/student/homework": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** My Homework */
        get: operations["my_homework_student_homework_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/student/homework/{homework_id}/submit": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Submit */
        post: operations["submit_student_homework__homework_id__submit_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/student/exams": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Upcoming Exams */
        get: operations["upcoming_exams_student_exams_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/student/results": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * My Results
         * @description Exams this student actually has marks for.
         */
        get: operations["my_results_student_results_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/student/results/{exam_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Report Card */
        get: operations["report_card_student_results__exam_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/parent/children": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Children */
        get: operations["children_parent_children_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/parent/children/{student_id}/summary": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Summary */
        get: operations["summary_parent_children__student_id__summary_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/parent/children/{student_id}/attendance": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Child Attendance */
        get: operations["child_attendance_parent_children__student_id__attendance_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/parent/children/{student_id}/homework": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Child Homework */
        get: operations["child_homework_parent_children__student_id__homework_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/parent/children/{student_id}/results": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Child Results */
        get: operations["child_results_parent_children__student_id__results_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/parent/children/{student_id}/results/{exam_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Child Report Card */
        get: operations["child_report_card_parent_children__student_id__results__exam_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/parent/children/{student_id}/profile": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Child Profile */
        get: operations["child_profile_parent_children__student_id__profile_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/parent/profile": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** My Profile */
        get: operations["my_profile_parent_profile_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/parent/notices": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** My Notices */
        get: operations["my_notices_parent_notices_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/parent/leave-requests": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** My Leave Requests */
        get: operations["my_leave_requests_parent_leave_requests_get"];
        put?: never;
        /**
         * Apply For Leave
         * @description A guardian asking for their own child to be away (§5.8.5).
         *
         *     Only a request: it changes the register when someone approves it.
         */
        post: operations["apply_for_leave_parent_leave_requests_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/parent/children/{student_id}/transport": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Child Transport
         * @description Which bus this child is on, where it stops and when (§5.6.8).
         *
         *     Scoped through `assert_can_read_student`, the same gate as everything else
         *     here — a guardian sees their own child's stop and nobody else's, and the
         *     driver's name and phone number are deliberately not in the payload.
         */
        get: operations["child_transport_parent_children__student_id__transport_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/parent/fees": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Invoices */
        get: operations["invoices_parent_fees_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/parent/fees/ledger": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Ledger */
        get: operations["ledger_parent_fees_ledger_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/parent/fees/pay": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Pay
         * @description Record a payment against the child's account.
         *
         *     Not "pay invoice 12": §0.10 defers the gateway, and even offline a parent
         *     hands over an amount, not a row. It settles the oldest dues first, which is
         *     both what a school does and what keeps the late-fee clock shortest.
         */
        post: operations["pay_parent_fees_pay_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/parent/fees/receipts/{payment_id}.pdf": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Receipt */
        get: operations["receipt_parent_fees_receipts__payment_id__pdf_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/public/{school_code}/admission/open": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Open Cycle
         * @description What a parent needs before starting: is the school taking applications,
         *     for which classes, and what should they bring.
         */
        get: operations["open_cycle_public__school_code__admission_open_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/public/{school_code}/admission/apply": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Apply */
        post: operations["apply_public__school_code__admission_apply_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/public/{school_code}/admission/status": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Application Status
         * @description Both the number and the child's date of birth, and one answer for every
         *     kind of miss: without that this endpoint enumerates other people's
         *     children.
         */
        get: operations["application_status_public__school_code__admission_status_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/health": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Health */
        get: operations["health_health_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
}
export type webhooks = Record<string, never>;
export interface components {
    schemas: {
        /** AccessToken */
        AccessToken: {
            /** Access Token */
            access_token: string;
            /**
             * Token Type
             * @default bearer
             */
            token_type?: string;
        };
        /**
         * AdmissionCategory
         * @description Why this applicant might be treated differently. Sibling and staff-ward
         *     are claims until verified against real records (§5.1.9(6)).
         * @enum {string}
         */
        AdmissionCategory: "general" | "sibling" | "staff_ward" | "management" | "rte" | "sports" | "alumni_child";
        /**
         * AdmissionCycleStatus
         * @enum {string}
         */
        AdmissionCycleStatus: "planning" | "open" | "closed" | "archived";
        /** AnnouncementCreate */
        AnnouncementCreate: {
            /** Title */
            title: string;
            /** Body */
            body: string;
            /** Class Section Id */
            class_section_id: number;
            /** @default class */
            audience?: components["schemas"]["NoticeAudience"];
        };
        /**
         * ApplicantDetails
         * @description Step 1 plus step 2 — everything needed to open a draft.
         */
        ApplicantDetails: {
            /** First Name */
            first_name: string;
            /** Last Name */
            last_name: string;
            /**
             * Date Of Birth
             * Format: date
             */
            date_of_birth: string;
            /** Gender */
            gender: string;
            /** Class Applying For */
            class_applying_for: string;
            /** Cycle Id */
            cycle_id?: number | null;
            /** Middle Name */
            middle_name?: string | null;
            /** Nationality */
            nationality?: string | null;
            /** Religion */
            religion?: string | null;
            /** Caste Category */
            caste_category?: string | null;
            /** Mother Tongue */
            mother_tongue?: string | null;
            /** Place Of Birth */
            place_of_birth?: string | null;
            /** Identification Marks */
            identification_marks?: string | null;
            /**
             * Is Single Child
             * @default false
             */
            is_single_child?: boolean;
            /** Aadhaar Last4 */
            aadhaar_last4?: string | null;
            /** Stream */
            stream?: string | null;
            /** Second Language */
            second_language?: string | null;
            /** Optional Subject */
            optional_subject?: string | null;
            /** Preferred Section */
            preferred_section?: string | null;
            /** @default general */
            admission_category?: components["schemas"]["AdmissionCategory"];
            /**
             * Transport Required
             * @default false
             */
            transport_required?: boolean;
            /** @default walk_in */
            source?: components["schemas"]["EnquirySource"];
            /** Enquiry Id */
            enquiry_id?: number | null;
            /** Previous Application Id */
            previous_application_id?: number | null;
        };
        /**
         * ApplicationFeePurpose
         * @description §5.1.9(15): the application fee is non-refundable, the admission fee is
         *     refundable per the policy recorded on the cycle. Keeping them apart is what
         *     makes that enforceable rather than a matter of memory.
         * @enum {string}
         */
        ApplicationFeePurpose: "application_fee" | "admission_fee";
        /**
         * ApplicationStatus
         * @description The pipeline of ERP_BLUEPRINT §5.1.7.
         *
         *     Forward moves are permission-gated; backward moves are allowed but always
         *     audited with a reason, because a real admissions office does reopen
         *     decisions and a system that forbids it just gets a second application
         *     record instead.
         * @enum {string}
         */
        ApplicationStatus: "draft" | "submitted" | "under_document_verification" | "documents_verified" | "documents_rejected" | "assessment_scheduled" | "assessment_completed" | "interview_scheduled" | "interview_completed" | "decision_pending" | "admitted" | "waitlisted" | "rejected" | "offer_issued" | "offer_accepted" | "offer_expired" | "fee_paid" | "enrolled" | "withdrawn_by_parent" | "cancelled_after_admission";
        /** ApplicationUpdate */
        ApplicationUpdate: {
            /** First Name */
            first_name?: string | null;
            /** Middle Name */
            middle_name?: string | null;
            /** Last Name */
            last_name?: string | null;
            /** Date Of Birth */
            date_of_birth?: string | null;
            /** Gender */
            gender?: string | null;
            /** Nationality */
            nationality?: string | null;
            /** Religion */
            religion?: string | null;
            /** Caste Category */
            caste_category?: string | null;
            /** Mother Tongue */
            mother_tongue?: string | null;
            /** Place Of Birth */
            place_of_birth?: string | null;
            /** Identification Marks */
            identification_marks?: string | null;
            /** Is Single Child */
            is_single_child?: boolean | null;
            /** Aadhaar Last4 */
            aadhaar_last4?: string | null;
            /** Class Applying For */
            class_applying_for?: string | null;
            /** Stream */
            stream?: string | null;
            /** Second Language */
            second_language?: string | null;
            /** Optional Subject */
            optional_subject?: string | null;
            /** Preferred Section */
            preferred_section?: string | null;
            admission_category?: components["schemas"]["AdmissionCategory"] | null;
            /** Transport Required */
            transport_required?: boolean | null;
            /** Address */
            address?: {
                [key: string]: unknown;
            } | null;
            /** Previous School */
            previous_school?: {
                [key: string]: unknown;
            } | null;
            /** Declarations */
            declarations?: {
                [key: string]: unknown;
            } | null;
            /** Age Override Reason */
            age_override_reason?: string | null;
        };
        /** ApplyIn */
        ApplyIn: {
            /** Employee Id */
            employee_id: number;
            /** Leave Type Id */
            leave_type_id: number;
            /**
             * From Date
             * Format: date
             */
            from_date: string;
            /**
             * To Date
             * Format: date
             */
            to_date: string;
            /** Reason */
            reason: string;
            /**
             * Is Half Day
             * @default false
             */
            is_half_day?: boolean;
        };
        /** AssessmentSchedule */
        AssessmentSchedule: {
            assessment_type: components["schemas"]["AssessmentType"];
            /**
             * Scheduled At
             * Format: date-time
             */
            scheduled_at: string;
            /** Venue */
            venue?: string | null;
            /** Seat No */
            seat_no?: string | null;
            /**
             * Subjects
             * @default []
             */
            subjects?: components["schemas"]["SubjectInput"][];
        };
        /**
         * AssessmentType
         * @description §5.1.2(4): assessment differs sharply by age. Nursery is an observation,
         *     class 6 is a written paper, class 11 is a previous-board result — one rigid
         *     "test marks" field fits none of them well.
         * @enum {string}
         */
        AssessmentType: "written_test" | "readiness_observation" | "previous_result_review";
        /** AssignIn */
        AssignIn: {
            /** Enrolment Id */
            enrolment_id: number;
            /** Fee Plan Id */
            fee_plan_id: number;
        };
        /** AssignmentStatusIn */
        AssignmentStatusIn: {
            status: components["schemas"]["TransportAssignmentStatus"];
            /** End Date */
            end_date?: string | null;
            /** Reason */
            reason?: string | null;
        };
        /** AttendanceDay */
        AttendanceDay: {
            /**
             * Date
             * Format: date
             */
            date: string;
            status: components["schemas"]["AttendanceStatus"];
        };
        /** AttendanceEntry */
        AttendanceEntry: {
            /** Student Id */
            student_id: number;
            status: components["schemas"]["AttendanceStatus"];
            /** Remarks */
            remarks?: string | null;
        };
        /** AttendanceMarkRequest */
        AttendanceMarkRequest: {
            /** Class Section Id */
            class_section_id: number;
            /**
             * Date
             * Format: date
             */
            date: string;
            /** Entries */
            entries: components["schemas"]["AttendanceEntry"][];
            /** Reason */
            reason?: string | null;
        };
        /** AttendanceMonth */
        AttendanceMonth: {
            /** Days */
            days: components["schemas"]["AttendanceDay"][];
            summary: components["schemas"]["AttendanceSummary"];
        };
        /**
         * AttendanceStatus
         * @description §5.8.4. `late` and `half_day` exist because a school records them and
         *     then has to answer "was the child here?" — collapsing them into present or
         *     absent loses the fact the office was actually asked about.
         *
         *     For the percentage, present and late count as attendance, half_day as half,
         *     and everything else as absence. Approved leave is still reported apart from
         *     unexcused absence, because to a parent those are not the same conversation.
         * @enum {string}
         */
        AttendanceStatus: "present" | "absent" | "late" | "half_day" | "leave" | "excused";
        /** AttendanceSummary */
        AttendanceSummary: {
            /** Present */
            present: number;
            /** Absent */
            absent: number;
            /** Leave */
            leave: number;
            /** Percent */
            percent: number | null;
        };
        /** AudienceIn */
        AudienceIn: {
            /** Kind */
            kind: string;
            /** Class Section Id */
            class_section_id?: number | null;
            /** Student Id */
            student_id?: number | null;
            /** Route Id */
            route_id?: number | null;
            /** Employee Id */
            employee_id?: number | null;
            /** Application Id */
            application_id?: number | null;
            /** Permission */
            permission?: string | null;
            /** Min Amount */
            min_amount?: number | null;
        };
        /** BandIn */
        BandIn: {
            /** Min Percent */
            min_percent: number | string;
            /** Grade */
            grade: string;
            /** Description */
            description?: string | null;
        };
        /** BatchDecision */
        BatchDecision: {
            /** Decisions */
            decisions: {
                [key: string]: unknown;
            }[];
        };
        /** Body_upload_document_admin_admission_applications__application_id__documents_post */
        Body_upload_document_admin_admission_applications__application_id__documents_post: {
            /**
             * Code
             * @description Document type code, e.g. birth_certificate
             */
            code: string;
            /** File */
            file: string;
        };
        /**
         * BroadcastIn
         * @description An emergency broadcast says what it is, and is confirmed in words.
         *
         *     §5.9.3 wants the confirmation on the screen. Requiring it in the payload
         *     means the API cannot be used to skip past the screen, which is the only
         *     way a confirmation is worth anything.
         */
        BroadcastIn: {
            /** Subject */
            subject: string;
            /** Body */
            body: string;
            /**
             * @default {
             *       "kind": "all_guardians"
             *     }
             */
            audience?: components["schemas"]["AudienceIn"];
            /** Confirm */
            confirm: boolean;
        };
        /** ChangePasswordRequest */
        ChangePasswordRequest: {
            /** Old Password */
            old_password: string;
            /** New Password */
            new_password: string;
        };
        /**
         * Channel
         * @description §0.11: email only for v1. The other two exist so the provider interface
         *     has something to be an interface *to*, and stay disabled per school until
         *     DLT registration exists — not so that a half-built SMS path can be
         *     switched on by accident.
         * @enum {string}
         */
        Channel: "email" | "sms" | "whatsapp";
        /** ChildRef */
        ChildRef: {
            /** Id */
            id: number;
            /** Name */
            name: string;
            /** Class Label */
            class_label: string;
            /** Admission No */
            admission_no: string;
        };
        /** ClassConfigInput */
        ClassConfigInput: {
            /** Class Name */
            class_name: string;
            /** Stream */
            stream?: string | null;
            /** Total Seats */
            total_seats: number;
            /** Reserved Seats */
            reserved_seats?: {
                [key: string]: number;
            } | null;
            /** Age On */
            age_on?: string | null;
            /** Min Age Years */
            min_age_years?: number | string | null;
            /** Max Age Years */
            max_age_years?: number | string | null;
            /**
             * Requires Test
             * @default false
             */
            requires_test?: boolean;
            /**
             * Requires Interview
             * @default false
             */
            requires_interview?: boolean;
            /** Required Document Codes */
            required_document_codes?: string[] | null;
        };
        /** ClassCreate */
        ClassCreate: {
            /** Class Name */
            class_name: string;
            /** Section */
            section: string;
            /** Class Teacher Id */
            class_teacher_id?: number | null;
            /** Capacity */
            capacity?: number | null;
            /** Stream */
            stream?: string | null;
            /** Room */
            room?: string | null;
            /** Academic Year Id */
            academic_year_id?: number | null;
        };
        /** ClassUpdate */
        ClassUpdate: {
            /** Class Teacher Id */
            class_teacher_id?: number | null;
        };
        /** CollectIn */
        CollectIn: {
            /** Enrolment Id */
            enrolment_id: number;
            /** Amount */
            amount: number | string;
            /**
             * Method
             * @default cash
             */
            method?: string;
            /** Instrument Ref */
            instrument_ref?: string | null;
            /** Idempotency Key */
            idempotency_key: string;
        };
        /** ComposeIn */
        ComposeIn: {
            audience: components["schemas"]["AudienceIn"];
            /** @default general */
            category?: components["schemas"]["MessageCategory"];
            /** Subject */
            subject?: string | null;
            /** Body */
            body?: string | null;
            /** Template Code */
            template_code?: string | null;
            /** @default email */
            channel?: components["schemas"]["Channel"];
            /**
             * Send Now
             * @default true
             */
            send_now?: boolean;
        };
        /** ConcessionIn */
        ConcessionIn: {
            /** Enrolment Id */
            enrolment_id: number;
            type: components["schemas"]["ConcessionType"];
            /** Reason */
            reason: string;
            /** Fee Head Id */
            fee_head_id?: number | null;
            /** Percent */
            percent?: number | string | null;
            /** Amount */
            amount?: number | string | null;
            /** Valid From */
            valid_from?: string | null;
            /** Valid To */
            valid_to?: string | null;
        };
        /**
         * ConcessionStatus
         * @description §5.5.9: a concession affects money only once someone approved it, and
         *     who approved it is exactly what an audit asks.
         * @enum {string}
         */
        ConcessionStatus: "requested" | "approved" | "rejected" | "expired";
        /**
         * ConcessionType
         * @enum {string}
         */
        ConcessionType: "sibling" | "staff_ward" | "rte" | "management" | "scholarship" | "other";
        /**
         * CrewIn
         * @description Every field optional and three-valued: absent means "leave it alone",
         *     null means "take it off". A PATCH that cannot say "remove the attendant"
         *     would need a second endpoint to do it.
         */
        CrewIn: {
            /** Vehicle Id */
            vehicle_id?: number | null;
            /** Driver Id */
            driver_id?: number | null;
            /** Attendant Id */
            attendant_id?: number | null;
            /** Clear */
            clear?: string[];
        };
        /** CustomFieldCreate */
        CustomFieldCreate: {
            entity: components["schemas"]["OwnerType"];
            /** Key */
            key: string;
            /** Label */
            label: string;
            field_type: components["schemas"]["CustomFieldType"];
            /** Options */
            options?: string[] | null;
            /**
             * Is Required
             * @default false
             */
            is_required?: boolean;
            /**
             * Sort Order
             * @default 100
             */
            sort_order?: number;
        };
        /**
         * CustomFieldType
         * @description What a school-defined attribute holds. Deliberately few: every type
         *     here has an obvious form control and an obvious validation rule.
         * @enum {string}
         */
        CustomFieldType: "text" | "number" | "date" | "boolean" | "select";
        /** CycleCreate */
        CycleCreate: {
            /** Academic Year Id */
            academic_year_id: number;
            /** Name */
            name: string;
            /** Starts On */
            starts_on?: string | null;
            /** Ends On */
            ends_on?: string | null;
            /**
             * Application Fee
             * @default 0
             */
            application_fee?: number | string;
            /**
             * Late Fee
             * @default 0
             */
            late_fee?: number | string;
            /**
             * Allow Online Applications
             * @default true
             */
            allow_online_applications?: boolean;
            /** Admission Fee Refund Policy */
            admission_fee_refund_policy?: string | null;
        };
        /** CycleUpdate */
        CycleUpdate: {
            /** Name */
            name?: string | null;
            status?: components["schemas"]["AdmissionCycleStatus"] | null;
            /** Starts On */
            starts_on?: string | null;
            /** Ends On */
            ends_on?: string | null;
            /** Application Fee */
            application_fee?: number | string | null;
            /** Late Fee */
            late_fee?: number | string | null;
            /** Allow Online Applications */
            allow_online_applications?: boolean | null;
            /** Admission Fee Refund Policy */
            admission_fee_refund_policy?: string | null;
        };
        /**
         * DayOfWeek
         * @enum {string}
         */
        DayOfWeek: "mon" | "tue" | "wed" | "thu" | "fri" | "sat";
        /** DecideIn */
        DecideIn: {
            /** Approve */
            approve: boolean;
            /** Reason */
            reason?: string | null;
        };
        /** DecisionIn */
        DecisionIn: {
            /** Note */
            note?: string | null;
            /**
             * Allow Exception
             * @default false
             */
            allow_exception?: boolean;
        };
        /** DecisionInput */
        DecisionInput: {
            decision: components["schemas"]["DecisionOutcome"];
            /** Reason */
            reason: string;
            /** Seat Category */
            seat_category?: string | null;
            /** Conditions */
            conditions?: string | null;
            /**
             * Over Allocation Approved
             * @default false
             */
            over_allocation_approved?: boolean;
        };
        /**
         * DecisionOutcome
         * @enum {string}
         */
        DecisionOutcome: "admitted" | "waitlisted" | "rejected";
        /** DepartmentIn */
        DepartmentIn: {
            /** Code */
            code: string;
            /** Name */
            name: string;
        };
        /** EmployeeCreate */
        EmployeeCreate: {
            /** Full Name */
            full_name: string;
            /** Employee Code */
            employee_code: string;
            /** @default teaching */
            employee_type?: components["schemas"]["EmployeeType"];
            /** Qualification */
            qualification?: string | null;
            /** Joining Date */
            joining_date?: string | null;
            /** Email */
            email?: string | null;
            /** Phone */
            phone?: string | null;
            /**
             * Password
             * @default Teacher@123
             */
            password?: string;
        };
        /**
         * EmployeeType
         * @enum {string}
         */
        EmployeeType: "teaching" | "administrative" | "support";
        /** EmployeeUpdate */
        EmployeeUpdate: {
            /** Full Name */
            full_name?: string | null;
            /** Qualification */
            qualification?: string | null;
            /** Email */
            email?: string | null;
            /** Phone */
            phone?: string | null;
        };
        /**
         * EnquiryChannel
         * @description How one interaction in the follow-up log happened.
         * @enum {string}
         */
        EnquiryChannel: "phone" | "visit" | "email" | "whatsapp" | "sms";
        /**
         * EnquiryCreate
         * @description Deliberately small. Screen 3 is a receptionist on the phone with sixty
         *     seconds; everything but a name and a number can arrive later.
         */
        EnquiryCreate: {
            /** Enquirer Name */
            enquirer_name: string;
            /** Mobile */
            mobile: string;
            /** Cycle Id */
            cycle_id?: number | null;
            /** Email */
            email?: string | null;
            /** Child Name */
            child_name?: string | null;
            /** Child Dob */
            child_dob?: string | null;
            /** Class Of Interest */
            class_of_interest?: string | null;
            /** @default walk_in */
            source?: components["schemas"]["EnquirySource"];
            /** Assigned To */
            assigned_to?: number | null;
            /** Next Follow Up On */
            next_follow_up_on?: string | null;
        };
        /**
         * EnquirySource
         * @enum {string}
         */
        EnquirySource: "walk_in" | "phone" | "website" | "referral" | "alumni" | "hoarding" | "digital_ad" | "other";
        /**
         * EnquiryStatus
         * @description A funnel stage, not a formality: a school takes 800 enquiries to fill
         *     120 seats, and conversion by source is a number management asks for
         *     (ERP_BLUEPRINT §5.1.7).
         * @enum {string}
         */
        EnquiryStatus: "new" | "contacted" | "interested" | "application_form_issued" | "converted" | "not_interested" | "lost_to_competitor" | "invalid";
        /** ExamCreate */
        ExamCreate: {
            /** Name */
            name: string;
            /** Term */
            term: string;
            /**
             * Start Date
             * Format: date
             */
            start_date: string;
            /**
             * End Date
             * Format: date
             */
            end_date: string;
            /** Scheme Component Id */
            scheme_component_id?: number | null;
        };
        /** ExamOut */
        ExamOut: {
            /** Id */
            id: number;
            /** Name */
            name: string;
            /** Term */
            term: string;
            /**
             * Start Date
             * Format: date
             */
            start_date: string;
            /**
             * End Date
             * Format: date
             */
            end_date: string;
            /** Scheme Component Id */
            scheme_component_id?: number | null;
        };
        /** ExamScheduleCreate */
        ExamScheduleCreate: {
            /** Class Section Id */
            class_section_id: number;
            /** Subject Id */
            subject_id: number;
            /**
             * Exam Date
             * Format: date
             */
            exam_date: string;
            /** Start Time */
            start_time?: string | null;
            /** Max Marks */
            max_marks: number | string;
        };
        /** ExamScheduleOut */
        ExamScheduleOut: {
            /** Id */
            id: number;
            /**
             * Marks Locked
             * @default false
             */
            marks_locked?: boolean;
            /** Exam Id */
            exam_id: number;
            /** Exam Name */
            exam_name: string;
            /** Class Section Id */
            class_section_id: number;
            /** Class Label */
            class_label: string;
            /** Subject Id */
            subject_id: number;
            /** Subject */
            subject: string;
            /**
             * Exam Date
             * Format: date
             */
            exam_date: string;
            /** Start Time */
            start_time: string | null;
            /** Max Marks */
            max_marks: string;
            /** Marks Entered */
            marks_entered: boolean;
        };
        /** ExitIn */
        ExitIn: {
            /**
             * Exited On
             * Format: date
             */
            exited_on: string;
            /** Reason */
            reason: string;
        };
        /**
         * FeeFrequency
         * @enum {string}
         */
        FeeFrequency: "monthly" | "one_time";
        /**
         * FeeHeadType
         * @description What kind of charge this is. `optional` is the one that matters
         *     operationally: transport and meals are billed only to who opted in, and a
         *     plan that cannot say so ends up charging every child for the bus.
         * @enum {string}
         */
        FeeHeadType: "recurring" | "one_time" | "optional";
        /**
         * Gender
         * @enum {string}
         */
        Gender: "male" | "female" | "other";
        /** GenerateIn */
        GenerateIn: {
            /** Month */
            month: number;
            /** Year */
            year: number;
        };
        /**
         * GuardianRelation
         * @description Who this adult is to the child. A closed list because it drives who may
         *     collect them from the gate, not just how a letter is addressed.
         * @enum {string}
         */
        GuardianRelation: "father" | "mother" | "grandparent" | "sibling" | "legal_guardian" | "other";
        /** HTTPValidationError */
        HTTPValidationError: {
            /** Detail */
            detail?: components["schemas"]["ValidationError"][];
        };
        /** HolidayIn */
        HolidayIn: {
            /**
             * Date
             * Format: date
             */
            date: string;
            /** Name */
            name: string;
            /** Academic Year Id */
            academic_year_id?: number | null;
        };
        /** HomeworkCreate */
        HomeworkCreate: {
            /** Class Section Id */
            class_section_id: number;
            /** Subject Id */
            subject_id: number;
            /** Title */
            title: string;
            /** Description */
            description?: string | null;
            /**
             * Due Date
             * Format: date
             */
            due_date: string;
        };
        /** HomeworkOut */
        HomeworkOut: {
            /** Id */
            id: number;
            /** Class Section Id */
            class_section_id: number;
            /** Class Label */
            class_label: string;
            /** Subject Id */
            subject_id: number;
            /** Subject */
            subject: string;
            /** Teacher Id */
            teacher_id: number;
            /** Teacher */
            teacher: string;
            /** Title */
            title: string;
            /** Description */
            description: string | null;
            /**
             * Assigned Date
             * Format: date
             */
            assigned_date: string;
            /**
             * Due Date
             * Format: date
             */
            due_date: string;
            /** Submitted Count */
            submitted_count: number;
            /** Total Students */
            total_students: number;
        };
        /** HomeworkUpdate */
        HomeworkUpdate: {
            /** Title */
            title?: string | null;
            /** Description */
            description?: string | null;
            /** Due Date */
            due_date?: string | null;
        };
        /** InteractionCreate */
        InteractionCreate: {
            channel: components["schemas"]["EnquiryChannel"];
            /** Notes */
            notes?: string | null;
            outcome?: components["schemas"]["EnquiryStatus"] | null;
            /** Next Follow Up On */
            next_follow_up_on?: string | null;
        };
        /**
         * InterviewRecommendation
         * @enum {string}
         */
        InterviewRecommendation: "strong_admit" | "admit" | "waitlist" | "reject";
        /** InterviewSchedule */
        InterviewSchedule: {
            /**
             * Scheduled At
             * Format: date-time
             */
            scheduled_at: string;
            /** Venue */
            venue?: string | null;
            /**
             * Panel Member Ids
             * @default []
             */
            panel_member_ids?: number[];
        };
        /**
         * InvoiceStatus
         * @description ERP_BLUEPRINT §5.5.7. `overdue` is stored as well as computed: the
         *     scheduled sweep moves it, and `fees.presented_status()` shows how an
         *     invoice reads right now without a GET writing anything.
         * @enum {string}
         */
        InvoiceStatus: "draft" | "issued" | "partially_paid" | "paid" | "overdue" | "voided" | "written_off";
        /** LeaveDecision */
        LeaveDecision: {
            /** Approve */
            approve: boolean;
            /** Note */
            note?: string | null;
        };
        /** LeaveIn */
        LeaveIn: {
            /** Student Id */
            student_id: number;
            /**
             * From Date
             * Format: date
             */
            from_date: string;
            /**
             * To Date
             * Format: date
             */
            to_date: string;
            /** @default sick */
            type?: components["schemas"]["LeaveType"];
            /** Reason */
            reason: string;
        };
        /**
         * LeaveStatus
         * @enum {string}
         */
        LeaveStatus: "applied" | "approved" | "rejected" | "cancelled";
        /**
         * LeaveType
         * @enum {string}
         */
        LeaveType: "sick" | "planned" | "emergency";
        /** LeaveTypeIn */
        LeaveTypeIn: {
            /** Code */
            code: string;
            /** Name */
            name: string;
            /** Annual Quota */
            annual_quota: number | string;
            /**
             * Is Paid
             * @default true
             */
            is_paid?: boolean;
        };
        /** LoginRequest */
        LoginRequest: {
            role: components["schemas"]["UserRole"];
            /** Login Id */
            login_id: string;
            /** Password */
            password: string;
            /** School Code */
            school_code?: string | null;
        };
        /** MarkRequest */
        MarkRequest: {
            /**
             * Date
             * Format: date
             */
            date: string;
            /** Entries */
            entries: components["schemas"]["app__api__admin__staff_attendance__MarkEntry"][];
            /** Reason */
            reason?: string | null;
        };
        /** MarksInput */
        MarksInput: {
            /** Obtained Marks */
            obtained_marks?: number | string | null;
            /** Total Marks */
            total_marks?: number | string | null;
            /**
             * Is Absent
             * @default false
             */
            is_absent?: boolean;
            /** Remarks */
            remarks?: string | null;
            /**
             * Subject Marks
             * @default {}
             */
            subject_marks?: {
                [key: string]: number | string;
            };
            /** Reason */
            reason?: string | null;
        };
        /** MarksRequest */
        MarksRequest: {
            /** Exam Schedule Id */
            exam_schedule_id: number;
            /** Entries */
            entries: components["schemas"]["app__schemas__common__MarkEntry"][];
            /** Reason */
            reason?: string | null;
        };
        /** MarksRosterRow */
        MarksRosterRow: {
            /** Student Id */
            student_id: number;
            /** Full Name */
            full_name: string;
            /** Roll No */
            roll_no: number;
            /** Marks Obtained */
            marks_obtained: string | null;
            /**
             * Is Absent
             * @default false
             */
            is_absent?: boolean;
            /**
             * Is Exempted
             * @default false
             */
            is_exempted?: boolean;
            /** Remarks */
            remarks?: string | null;
        };
        /** MeOut */
        MeOut: {
            user: components["schemas"]["UserOut"];
            /**
             * Permissions
             * @default []
             */
            permissions?: string[];
            /**
             * Roles
             * @default []
             */
            roles?: string[];
            /** School Code */
            school_code?: string | null;
            /** School Name */
            school_name?: string | null;
            /** Academic Year */
            academic_year?: string | null;
            /**
             * Modules
             * @default []
             */
            modules?: string[];
            /** Admission No */
            admission_no?: string | null;
            /** Class Label */
            class_label?: string | null;
            /** Roll No */
            roll_no?: number | null;
            /** Employee Id */
            employee_id?: string | null;
            /** Sections */
            sections?: string[] | null;
            /** Children */
            children?: components["schemas"]["ChildRef"][] | null;
        };
        /** MedicalInput */
        MedicalInput: {
            /** Blood Group */
            blood_group?: string | null;
            /** Known Allergies */
            known_allergies?: string | null;
            /** Chronic Conditions */
            chronic_conditions?: string | null;
            /** Regular Medication */
            regular_medication?: string | null;
            /** Physical Disability */
            physical_disability?: string | null;
            /** Learning Needs */
            learning_needs?: string | null;
            /** Vision Hearing Notes */
            vision_hearing_notes?: string | null;
            /** Emergency Doctor */
            emergency_doctor?: string | null;
            /** Emergency Doctor Phone */
            emergency_doctor_phone?: string | null;
            /**
             * Consent For Emergency Treatment
             * @default false
             */
            consent_for_emergency_treatment?: boolean;
        };
        /**
         * MessageCategory
         * @description What a message is about, which is what opt-out is decided against.
         *
         *     §5.9.9 draws the line: informational messages respect an opt-out, statutory
         *     and emergency ones override it. `MANDATORY_CATEGORIES` in
         *     `services/comms.py` is that line, written down.
         * @enum {string}
         */
        MessageCategory: "emergency" | "attendance" | "fees" | "examination" | "transport" | "admission" | "hr" | "general";
        /**
         * MessageStatus
         * @description §5.9.7, minus `sending` as a resting state: dispatch is a job, so a
         *     message is either waiting to be picked up or has been.
         * @enum {string}
         */
        MessageStatus: "draft" | "scheduled" | "sending" | "completed" | "failed" | "cancelled";
        /** NoteIn */
        NoteIn: {
            /** Note */
            note?: string | null;
        };
        /**
         * NoticeAudience
         * @enum {string}
         */
        NoticeAudience: "all" | "students" | "parents" | "teachers" | "class";
        /** NoticeCreate */
        NoticeCreate: {
            /** Title */
            title: string;
            /** Body */
            body: string;
            audience: components["schemas"]["NoticeAudience"];
            /** Class Section Id */
            class_section_id?: number | null;
            /**
             * Notify
             * @default false
             */
            notify?: boolean;
        };
        /** NoticeOut */
        NoticeOut: {
            /** Id */
            id: number;
            /** Title */
            title: string;
            /** Body */
            body: string;
            audience: components["schemas"]["NoticeAudience"];
            /** Class Section Id */
            class_section_id: number | null;
            /** Class Label */
            class_label: string | null;
            /** Published By */
            published_by: string;
            /**
             * Published At
             * Format: date-time
             */
            published_at: string;
            /** Message Id */
            message_id?: number | null;
        };
        /** OfferInput */
        OfferInput: {
            /**
             * Expires On
             * Format: date
             */
            expires_on: string;
            /** Offer Amount */
            offer_amount?: number | string | null;
        };
        /** OfferResponse */
        OfferResponse: {
            /** Accepted */
            accepted: boolean;
            /** Reason */
            reason?: string | null;
        };
        /**
         * OwnerType
         * @description What a document is attached to. `application` exists before the student
         *     does, which is why documents are polymorphic rather than a student column.
         * @enum {string}
         */
        OwnerType: "student" | "application" | "guardian" | "employee" | "vehicle" | "school";
        /** Page */
        Page: {
            /** Items */
            items: unknown[];
            /** Total */
            total: number;
            /** Page */
            page: number;
            /** Page Size */
            page_size: number;
        };
        /** PanelFeedback */
        PanelFeedback: {
            /** Child Rating */
            child_rating?: number | null;
            /** Parent Rating */
            parent_rating?: number | null;
            recommendation?: components["schemas"]["InterviewRecommendation"] | null;
            /** Notes */
            notes?: string | null;
            /** Reason */
            reason?: string | null;
        };
        /** PayIn */
        PayIn: {
            /** Student Id */
            student_id: number;
            /** Amount */
            amount: number | string;
            /** Idempotency Key */
            idempotency_key: string;
        };
        /** PaymentInput */
        PaymentInput: {
            purpose: components["schemas"]["ApplicationFeePurpose"];
            /** Amount */
            amount: number | string;
            /**
             * Method
             * @default cash
             */
            method?: string;
            /** Reference */
            reference?: string | null;
            /** Idempotency Key */
            idempotency_key?: string | null;
        };
        /** PeriodIn */
        PeriodIn: {
            /** Period No */
            period_no: number;
            /**
             * Start Time
             * Format: time
             */
            start_time: string;
            /**
             * End Time
             * Format: time
             */
            end_time: string;
            /** Name */
            name?: string | null;
            /**
             * Is Break
             * @default false
             */
            is_break?: boolean;
        };
        /** PlanIn */
        PlanIn: {
            /** Academic Year Id */
            academic_year_id: number;
            /** Name */
            name: string;
            /** Class Name */
            class_name?: string | null;
            /**
             * Items
             * @default []
             */
            items?: components["schemas"]["PlanItemIn"][];
        };
        /** PlanItemIn */
        PlanItemIn: {
            /** Fee Head Id */
            fee_head_id: number;
            /** Amount */
            amount: number | string;
            /** @default monthly */
            frequency?: components["schemas"]["FeeFrequency"];
        };
        /** PreferenceIn */
        PreferenceIn: {
            category: components["schemas"]["MessageCategory"];
            /** @default email */
            channel?: components["schemas"]["Channel"];
            /**
             * Opted Out
             * @default true
             */
            opted_out?: boolean;
        };
        /** PublicApplication */
        PublicApplication: {
            /** First Name */
            first_name: string;
            /** Last Name */
            last_name: string;
            /** Middle Name */
            middle_name?: string | null;
            /**
             * Date Of Birth
             * Format: date
             */
            date_of_birth: string;
            /** Gender */
            gender: string;
            /** Class Applying For */
            class_applying_for: string;
            /** Stream */
            stream?: string | null;
            /** Mother Tongue */
            mother_tongue?: string | null;
            /** Caste Category */
            caste_category?: string | null;
            /** @default general */
            admission_category?: components["schemas"]["AdmissionCategory"];
            /**
             * Transport Required
             * @default false
             */
            transport_required?: boolean;
            /** Address */
            address?: {
                [key: string]: unknown;
            } | null;
            /** Previous School */
            previous_school?: {
                [key: string]: unknown;
            } | null;
            /** Guardians */
            guardians: components["schemas"]["PublicGuardian"][];
            /** @default website */
            heard_about_us?: components["schemas"]["EnquirySource"];
            /**
             * Information Accuracy
             * @default false
             */
            information_accuracy?: boolean;
            /**
             * School Rules Accepted
             * @default false
             */
            school_rules_accepted?: boolean;
            /**
             * Data Processing Consent
             * @default false
             */
            data_processing_consent?: boolean;
            /** Photo Media Consent */
            photo_media_consent?: boolean | null;
            /** Website */
            website?: string | null;
        };
        /** PublicGuardian */
        PublicGuardian: {
            relation: components["schemas"]["GuardianRelation"];
            /** Full Name */
            full_name: string;
            /** Mobile */
            mobile: string;
            /** Email */
            email?: string | null;
            /** Occupation */
            occupation?: string | null;
            /**
             * Is Primary
             * @default false
             */
            is_primary?: boolean;
        };
        /** RefreshRequest */
        RefreshRequest: {
            /** Refresh Token */
            refresh_token: string;
        };
        /** ReleaseRequest */
        ReleaseRequest: {
            /** Reason */
            reason: string;
        };
        /** ReportCard */
        ReportCard: {
            /** Exam Id */
            exam_id: number;
            /** Exam Name */
            exam_name: string;
            /** Student Id */
            student_id: number;
            /** Student Name */
            student_name: string;
            /** Class Label */
            class_label: string;
            /** Rows */
            rows: components["schemas"]["ReportCardRow"][];
            /** Total Obtained */
            total_obtained: string;
            /** Total Max */
            total_max: string;
            /** Overall Percent */
            overall_percent: number | null;
            /** Overall Grade */
            overall_grade: string | null;
        };
        /** ReportCardRow */
        ReportCardRow: {
            /** Subject */
            subject: string;
            /** Marks Obtained */
            marks_obtained: string | null;
            /** Max Marks */
            max_marks: string;
            /** Percent */
            percent: number | null;
            /** Grade */
            grade: string | null;
            /**
             * Is Absent
             * @default false
             */
            is_absent?: boolean;
            /**
             * Is Exempted
             * @default false
             */
            is_exempted?: boolean;
        };
        /** RollRow */
        RollRow: {
            /** Student Id */
            student_id: number;
            /** Full Name */
            full_name: string;
            /** Roll No */
            roll_no: number;
            status?: components["schemas"]["AttendanceStatus"] | null;
            /**
             * Corrected
             * @default false
             */
            corrected?: boolean;
            /** Remarks */
            remarks?: string | null;
        };
        /** RouteIn */
        RouteIn: {
            /** Code */
            code: string;
            /** Name */
            name: string;
            /** Distance Km */
            distance_km?: number | string | null;
        };
        /**
         * RouteStatus
         * @enum {string}
         */
        RouteStatus: "planned" | "active" | "suspended" | "closed";
        /** RouteStatusIn */
        RouteStatusIn: {
            status: components["schemas"]["RouteStatus"];
            /** Reason */
            reason: string;
        };
        /** RunIn */
        RunIn: {
            /** Year */
            year: number;
            /** Month */
            month: number;
            /**
             * Supplementary
             * @default false
             */
            supplementary?: boolean;
        };
        /** ScaleIn */
        ScaleIn: {
            /** Name */
            name: string;
            /** Bands */
            bands: components["schemas"]["BandIn"][];
            /**
             * Activate
             * @default false
             */
            activate?: boolean;
        };
        /** SchemeIn */
        SchemeIn: {
            /** Name */
            name: string;
            /** Components */
            components?: components["schemas"]["app__api__admin__schemes__ComponentIn"][] | null;
            /** Academic Year Id */
            academic_year_id?: number | null;
            /**
             * Activate
             * @default false
             */
            activate?: boolean;
        };
        /** SiblingInput */
        SiblingInput: {
            /** Student Id */
            student_id?: number | null;
            /** Name */
            name?: string | null;
            /** Age */
            age?: number | null;
            /** School Name */
            school_name?: string | null;
        };
        /** SlabIn */
        SlabIn: {
            /** Name */
            name: string;
            /** Monthly Amount */
            monthly_amount: number | string;
            /**
             * Is Active
             * @default true
             */
            is_active?: boolean;
        };
        /** SlotIn */
        SlotIn: {
            /** Class Section Id */
            class_section_id: number;
            day_of_week: components["schemas"]["DayOfWeek"];
            /** Period Id */
            period_id: number;
            /** Subject Id */
            subject_id: number;
            /** Teacher Id */
            teacher_id: number;
            /** Room */
            room?: string | null;
            /** Override Reason */
            override_reason?: string | null;
        };
        /** SlotOut */
        SlotOut: {
            /** Period */
            period: number;
            /** Day Of Week */
            day_of_week: string;
            /**
             * Start Time
             * Format: time
             */
            start_time: string;
            /**
             * End Time
             * Format: time
             */
            end_time: string;
            /** Class Section Id */
            class_section_id: number;
            /** Class Label */
            class_label: string;
            /** Subject */
            subject: string;
            /** Teacher */
            teacher: string;
            /** Room */
            room: string | null;
        };
        /** StatusMove */
        StatusMove: {
            status: components["schemas"]["ApplicationStatus"];
            /** Reason */
            reason?: string | null;
        };
        /** StatutoryIn */
        StatutoryIn: {
            /** Pan */
            pan?: string | null;
            /** Uan */
            uan?: string | null;
            /** Esi Number */
            esi_number?: string | null;
            /** Bank Account No */
            bank_account_no?: string | null;
            /** Bank Ifsc */
            bank_ifsc?: string | null;
            /** Bank Name */
            bank_name?: string | null;
        };
        /** StopIn */
        StopIn: {
            /** Sequence */
            sequence: number;
            /** Name */
            name: string;
            /** Landmark */
            landmark?: string | null;
            /**
             * Pickup Time
             * Format: time
             */
            pickup_time: string;
            /** Drop Time */
            drop_time?: string | null;
            /** Fee Slab Id */
            fee_slab_id?: number | null;
        };
        /** StructureIn */
        StructureIn: {
            /** Employee Id */
            employee_id: number;
            /**
             * Effective From
             * Format: date
             */
            effective_from: string;
            /** Monthly Gross */
            monthly_gross: number | string;
            /** Overrides */
            overrides?: {
                [key: string]: number | string;
            } | null;
            /** Note */
            note?: string | null;
        };
        /** StudentCreate */
        StudentCreate: {
            /** Full Name */
            full_name: string;
            /** Admission No */
            admission_no?: string | null;
            /** Class Section Id */
            class_section_id: number;
            /** Roll No */
            roll_no: number;
            /** Dob */
            dob?: string | null;
            gender?: components["schemas"]["Gender"] | null;
            /** Address */
            address?: string | null;
            /** Admission Date */
            admission_date?: string | null;
            /** Phone */
            phone?: string | null;
            /** Email */
            email?: string | null;
            /**
             * Password
             * @default Student@123
             */
            password?: string;
            guardian?: components["schemas"]["app__api__admin__students__GuardianInput"] | null;
            /** Guardian Id */
            guardian_id?: number | null;
            /** Custom */
            custom?: {
                [key: string]: unknown;
            } | null;
        };
        /** StudentHomeworkOut */
        StudentHomeworkOut: {
            /** Id */
            id: number;
            /** Class Section Id */
            class_section_id: number;
            /** Class Label */
            class_label: string;
            /** Subject Id */
            subject_id: number;
            /** Subject */
            subject: string;
            /** Teacher Id */
            teacher_id: number;
            /** Teacher */
            teacher: string;
            /** Title */
            title: string;
            /** Description */
            description: string | null;
            /**
             * Assigned Date
             * Format: date
             */
            assigned_date: string;
            /**
             * Due Date
             * Format: date
             */
            due_date: string;
            /** Submitted Count */
            submitted_count: number;
            /** Total Students */
            total_students: number;
            /** Submitted */
            submitted: boolean;
            /** Submitted At */
            submitted_at: string | null;
            /** Late */
            late: boolean;
            /** Answer Text */
            answer_text: string | null;
        };
        /** StudentUpdate */
        StudentUpdate: {
            /** Full Name */
            full_name?: string | null;
            /** Class Section Id */
            class_section_id?: number | null;
            /** Roll No */
            roll_no?: number | null;
            /** Dob */
            dob?: string | null;
            gender?: components["schemas"]["Gender"] | null;
            /** Address */
            address?: string | null;
            /** Phone */
            phone?: string | null;
            /** Email */
            email?: string | null;
            /** Custom */
            custom?: {
                [key: string]: unknown;
            } | null;
        };
        /** SubjectInput */
        SubjectInput: {
            /** Subject */
            subject: string;
            /** Max Marks */
            max_marks: number | string;
        };
        /** SubmissionRow */
        SubmissionRow: {
            /** Student Id */
            student_id: number;
            /** Full Name */
            full_name: string;
            /** Roll No */
            roll_no: number;
            /** Submitted */
            submitted: boolean;
            /** Submitted At */
            submitted_at: string | null;
            /** Late */
            late: boolean;
            /** Answer Text */
            answer_text: string | null;
        };
        /** SubmitRequest */
        SubmitRequest: {
            /** Answer Text */
            answer_text: string;
        };
        /** SubstitutionIn */
        SubstitutionIn: {
            /** Slot Id */
            slot_id: number;
            /**
             * Date
             * Format: date
             */
            date: string;
            /** Substitute Teacher Id */
            substitute_teacher_id?: number | null;
            /** Reason */
            reason: string;
        };
        /** TemplateIn */
        TemplateIn: {
            /** Code */
            code: string;
            /** Name */
            name: string;
            category: components["schemas"]["MessageCategory"];
            /** Subject */
            subject: string;
            /** Body */
            body: string;
            /** @default email */
            channel?: components["schemas"]["Channel"];
        };
        /** TokenPair */
        TokenPair: {
            /** Access Token */
            access_token: string;
            /** Refresh Token */
            refresh_token: string;
            /**
             * Token Type
             * @default bearer
             */
            token_type?: string;
            user: components["schemas"]["UserOut"];
        };
        /**
         * TransportAssignmentStatus
         * @description §5.6.7. `ended` is not a delete: the row stays so the history of who rode
         *     which bus survives, and only the billing stops (§5.6.9).
         * @enum {string}
         */
        TransportAssignmentStatus: "requested" | "active" | "suspended" | "ended";
        /**
         * TransportDirection
         * @description Which legs of the journey a child rides. `both` is the ordinary case.
         * @enum {string}
         */
        TransportDirection: "pickup" | "drop" | "both";
        /** UnlockRequest */
        UnlockRequest: {
            /** Reason */
            reason: string;
        };
        /** UserOut */
        UserOut: {
            /** Id */
            id: number;
            role: components["schemas"]["UserRole"];
            /** Login Id */
            login_id: string;
            /** Full Name */
            full_name: string;
            /** Email */
            email?: string | null;
            /** Phone */
            phone?: string | null;
            /** Photo Url */
            photo_url?: string | null;
        };
        /**
         * UserRole
         * @enum {string}
         */
        UserRole: "admin" | "teacher" | "parent" | "student";
        /** ValidationError */
        ValidationError: {
            /** Location */
            loc: (string | number)[];
            /** Message */
            msg: string;
            /** Error Type */
            type: string;
            /** Input */
            input?: unknown;
            /** Context */
            ctx?: Record<string, never>;
        };
        /** VehicleIn */
        VehicleIn: {
            /** Registration No */
            registration_no: string;
            /** Make Model */
            make_model?: string | null;
            /** Capacity */
            capacity: number;
            /** @default owned */
            ownership?: components["schemas"]["VehicleOwnership"];
            /** Gps Device Id */
            gps_device_id?: string | null;
        };
        /**
         * VehicleOwnership
         * @enum {string}
         */
        VehicleOwnership: "owned" | "hired";
        /**
         * VehicleStatus
         * @description ERP_BLUEPRINT §5.6.7. Only `active` may carry children: the other three
         *     are the reasons a bus is off the road, kept distinct because "in the
         *     workshop this week" and "sold" are not the same operational fact.
         * @enum {string}
         */
        VehicleStatus: "active" | "under_maintenance" | "grounded" | "retired";
        /** VehicleStatusIn */
        VehicleStatusIn: {
            status: components["schemas"]["VehicleStatus"];
            /** Reason */
            reason: string;
        };
        /** Verdict */
        Verdict: {
            /** Approved */
            approved: boolean;
            /** Reason */
            reason?: string | null;
            /**
             * Original Seen
             * @default false
             */
            original_seen?: boolean;
        };
        /** GuardianInput */
        app__api__admin__applications__GuardianInput: {
            relation: components["schemas"]["GuardianRelation"];
            /** Full Name */
            full_name: string;
            /** Mobile */
            mobile: string;
            /** Date Of Birth */
            date_of_birth?: string | null;
            /** Qualification */
            qualification?: string | null;
            /** Occupation */
            occupation?: string | null;
            /** Designation */
            designation?: string | null;
            /** Organisation */
            organisation?: string | null;
            /** Annual Income Band */
            annual_income_band?: string | null;
            /** Office Address */
            office_address?: string | null;
            /** Alternate Mobile */
            alternate_mobile?: string | null;
            /** Email */
            email?: string | null;
            /**
             * Is Primary
             * @default false
             */
            is_primary?: boolean;
            /**
             * Is Emergency Contact
             * @default false
             */
            is_emergency_contact?: boolean;
            /**
             * Is Authorised For Pickup
             * @default false
             */
            is_authorised_for_pickup?: boolean;
            /**
             * Is School Alumnus
             * @default false
             */
            is_school_alumnus?: boolean;
            /**
             * Is School Staff
             * @default false
             */
            is_school_staff?: boolean;
            /** Employee Id */
            employee_id?: number | null;
        };
        /** HeadIn */
        app__api__admin__fee_setup__HeadIn: {
            /** Name */
            name: string;
            /** Code */
            code: string;
            /** @default recurring */
            type?: components["schemas"]["FeeHeadType"];
            /**
             * Is Refundable
             * @default false
             */
            is_refundable?: boolean;
            /** Gl Code */
            gl_code?: string | null;
            /**
             * Is Active
             * @default true
             */
            is_active?: boolean;
        };
        /** ReasonIn */
        app__api__admin__fees__ReasonIn: {
            /** Reason */
            reason: string;
        };
        /** AssignmentIn */
        app__api__admin__hr__AssignmentIn: {
            /** Department Id */
            department_id?: number | null;
            /** Designation */
            designation?: string | null;
            /** Reporting To Id */
            reporting_to_id?: number | null;
        };
        /** HeadIn */
        app__api__admin__hr__HeadIn: {
            /** Head Employee Id */
            head_employee_id?: number | null;
        };
        /** ComponentIn */
        app__api__admin__payroll__ComponentIn: {
            /** Value */
            value?: number | string | null;
            /** Active */
            active?: boolean | null;
            /** Sequence */
            sequence?: number | null;
            /** Applies Below Gross */
            applies_below_gross?: number | string | null;
        };
        /** ReasonIn */
        app__api__admin__payroll__ReasonIn: {
            /** Reason */
            reason: string;
        };
        /** ComponentIn */
        app__api__admin__schemes__ComponentIn: {
            /** Code */
            code: string;
            /** Name */
            name: string;
            /** Term */
            term: string;
            /** Max Marks */
            max_marks: number | string;
        };
        /** SettingsUpdate */
        app__api__admin__settings__SettingsUpdate: {
            /** Values */
            values: {
                [key: string]: unknown;
            };
        };
        /** MarkEntry */
        app__api__admin__staff_attendance__MarkEntry: {
            /** Employee Id */
            employee_id: number;
            status: components["schemas"]["AttendanceStatus"];
            /** Check In */
            check_in?: string | null;
            /** Check Out */
            check_out?: string | null;
            /** Remarks */
            remarks?: string | null;
        };
        /** ReasonIn */
        app__api__admin__staff_leave__ReasonIn: {
            /** Reason */
            reason: string;
        };
        /**
         * SettingsUpdate
         * @description Replaces the bare `dict` this endpoint used to accept: an admin write
         *     with no validation was a recorded defect, and settings now drive billing
         *     and branding for a whole tenant.
         */
        app__api__admin__stats__SettingsUpdate: {
            /** Academic Year */
            academic_year?: string | null;
            /** Name */
            name?: string | null;
            /** Address */
            address?: string | null;
            /** City */
            city?: string | null;
            /** State */
            state?: string | null;
            /** Pincode */
            pincode?: string | null;
            /** Phone */
            phone?: string | null;
            /** Email */
            email?: string | null;
            /** Website */
            website?: string | null;
            /** Logo Url */
            logo_url?: string | null;
            /** Primary Color */
            primary_color?: string | null;
            /** Board */
            board?: string | null;
            /** Affiliation No */
            affiliation_no?: string | null;
        };
        /** GuardianInput */
        app__api__admin__students__GuardianInput: {
            /** Full Name */
            full_name: string;
            /** Phone */
            phone: string;
            /** @default father */
            relation?: components["schemas"]["GuardianRelation"];
            /** Occupation */
            occupation?: string | null;
            /**
             * Password
             * @default Parent@123
             */
            password?: string;
        };
        /** AssignmentIn */
        app__api__admin__transport__AssignmentIn: {
            /** Student Id */
            student_id: number;
            /** Route Stop Id */
            route_stop_id: number;
            /** @default both */
            direction?: components["schemas"]["TransportDirection"];
            /**
             * Start Date
             * Format: date
             */
            start_date: string;
        };
        /** MarkEntry */
        app__schemas__common__MarkEntry: {
            /** Student Id */
            student_id: number;
            /** Marks Obtained */
            marks_obtained?: number | string | null;
            /**
             * Is Absent
             * @default false
             */
            is_absent?: boolean;
            /**
             * Is Exempted
             * @default false
             */
            is_exempted?: boolean;
            /** Remarks */
            remarks?: string | null;
        };
    };
    responses: never;
    parameters: never;
    requestBodies: never;
    headers: never;
    pathItems: never;
}
export type $defs = Record<string, never>;
export interface operations {
    login_auth_login_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["LoginRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TokenPair"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    refresh_auth_refresh_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RefreshRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AccessToken"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    me_auth_me_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MeOut"];
                };
            };
        };
    };
    change_password_auth_change_password_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ChangePasswordRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    dashboard_stats_admin_dashboard_stats_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
        };
    };
    get_settings_admin_settings_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
        };
    };
    update_settings_admin_settings_patch: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["app__api__admin__stats__SettingsUpdate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    grade_bands_admin_grade_bands_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    }[];
                };
            };
        };
    };
    list_students_admin_students_get: {
        parameters: {
            query?: {
                class_section_id?: number | null;
                q?: string | null;
                page?: number;
                page_size?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Page"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_student_admin_students_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["StudentCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    export_students_admin_students_export_get: {
        parameters: {
            query?: {
                class_section_id?: number | null;
                q?: string | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    student_detail_admin_students__student_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                student_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    deactivate_student_admin_students__student_id__delete: {
        parameters: {
            query: {
                /** @description Why this student is being deactivated. Recorded in the audit log. */
                reason: string;
            };
            header?: never;
            path: {
                student_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_student_admin_students__student_id__patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                student_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["StudentUpdate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_teachers_admin_teachers_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    }[];
                };
            };
        };
    };
    create_teacher_admin_teachers_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["EmployeeCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    deactivate_teacher_admin_teachers__teacher_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                teacher_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_teacher_admin_teachers__teacher_id__patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                teacher_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["EmployeeUpdate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_classes_admin_classes_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    }[];
                };
            };
        };
    };
    create_class_admin_classes_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ClassCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_class_admin_classes__class_id__patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                class_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ClassUpdate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    class_roster_admin_classes__class_id__students_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                class_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    }[];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_subjects_admin_subjects_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    }[];
                };
            };
        };
    };
    timetable_admin_timetable_get: {
        parameters: {
            query: {
                class_section_id: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SlotOut"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_exams_admin_exams_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ExamOut"][];
                };
            };
        };
    };
    create_exam_admin_exams_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ExamCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ExamOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    exam_schedule_admin_exams__exam_id__schedule_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                exam_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ExamScheduleOut"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    add_paper_admin_exams__exam_id__schedule_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                exam_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ExamScheduleCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ExamScheduleOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    lock_paper_admin_exams_papers__exam_schedule_id__lock_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                exam_schedule_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ExamScheduleOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    unlock_paper_admin_exams_papers__exam_schedule_id__unlock_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                exam_schedule_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["UnlockRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ExamScheduleOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    paper_marks_admin_exams_papers__exam_schedule_id__marks_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                exam_schedule_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MarksRosterRow"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    enter_paper_marks_admin_exams_papers__exam_schedule_id__marks_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                exam_schedule_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["MarksRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MarksRosterRow"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_scales_admin_grading_scales_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    }[];
                };
            };
        };
    };
    create_scale_admin_grading_scales_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ScaleIn"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    replace_bands_admin_grading_scales__scale_id__bands_put: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                scale_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["BandIn"][];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    activate_admin_grading_scales__scale_id__activate_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                scale_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_schemes_admin_assessment_schemes_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    }[];
                };
            };
        };
    };
    create_scheme_admin_assessment_schemes_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["SchemeIn"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    replace_components_admin_assessment_schemes__scheme_id__components_put: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                scheme_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["app__api__admin__schemes__ComponentIn"][];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    activate_admin_assessment_schemes__scheme_id__activate_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                scheme_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    preview_admin_report_cards_preview_get: {
        parameters: {
            query: {
                enrolment_id: number;
                term: string;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    readiness_admin_report_cards_readiness_get: {
        parameters: {
            query: {
                enrolment_id: number;
                term: string;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    publish_admin_report_cards_publish_post: {
        parameters: {
            query: {
                enrolment_id: number;
                term: string;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    issued_admin_report_cards__publication_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                publication_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_published_admin_report_cards_get: {
        parameters: {
            query?: {
                term?: string | null;
                class_section_id?: number | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    }[];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    release_admin_report_cards__publication_id__release_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                publication_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ReleaseRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_departments_admin_departments_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    }[];
                };
            };
        };
    };
    create_department_admin_departments_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["DepartmentIn"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    set_head_admin_departments__department_id__head_put: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                department_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["app__api__admin__hr__HeadIn"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_employees_admin_employees_get: {
        parameters: {
            query?: {
                department_id?: number | null;
                /** @description Past staff are kept forever; they are simply not the default answer to 'who works here'. */
                include_exited?: boolean;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    }[];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    employee_admin_employees__employee_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                employee_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    assign_admin_employees__employee_id__assignment_put: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                employee_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["app__api__admin__hr__AssignmentIn"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    statutory_admin_employees__employee_id__statutory_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                employee_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    set_statutory_admin_employees__employee_id__statutory_put: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                employee_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["StatutoryIn"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    allocations_admin_employees__employee_id__allocations_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                employee_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    record_exit_admin_employees__employee_id__exit_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                employee_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ExitIn"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_types_admin_staff_leave_types_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    }[];
                };
            };
        };
    };
    create_type_admin_staff_leave_types_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["LeaveTypeIn"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    balances_admin_staff_leave_balances__employee_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                employee_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    }[];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_requests_admin_staff_leave_get: {
        parameters: {
            query?: {
                employee_id?: number | null;
                request_status?: components["schemas"]["LeaveStatus"] | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    }[];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    apply_admin_staff_leave_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ApplyIn"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    affected_admin_staff_leave__request_id__affected_periods_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                request_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    }[];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    approve_admin_staff_leave__request_id__approve_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                request_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["DecisionIn"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    reject_admin_staff_leave__request_id__reject_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                request_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["app__api__admin__staff_leave__ReasonIn"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    cancel_admin_staff_leave__request_id__cancel_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                request_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["app__api__admin__staff_leave__ReasonIn"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    roll_admin_staff_attendance_get: {
        parameters: {
            query: {
                date: string;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    }[];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    mark_admin_staff_attendance_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["MarkRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    }[];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    summary_admin_staff_attendance_summary__employee_id__get: {
        parameters: {
            query: {
                from: string;
                to: string;
            };
            header?: never;
            path: {
                employee_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    components_admin_payroll_components_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    }[];
                };
            };
        };
    };
    update_component_admin_payroll_components__component_id__put: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                component_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["app__api__admin__payroll__ComponentIn"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    structure_admin_payroll_structures__employee_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                employee_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    } | null;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    set_structure_admin_payroll_structures_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["StructureIn"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    preview_admin_payroll_preview__employee_id__get: {
        parameters: {
            query: {
                year: number;
                month: number;
            };
            header?: never;
            path: {
                employee_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_runs_admin_payroll_runs_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    }[];
                };
            };
        };
    };
    open_run_admin_payroll_runs_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RunIn"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    calculate_admin_payroll_runs__run_id__calculate_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                run_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    approve_admin_payroll_runs__run_id__approve_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                run_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["NoteIn"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    mark_paid_admin_payroll_runs__run_id__paid_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                run_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    discard_admin_payroll_runs__run_id__discard_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                run_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["app__api__admin__payroll__ReasonIn"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    payslips_admin_payroll_runs__run_id__payslips_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                run_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    }[];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    payslip_admin_payroll_payslips__payslip_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                payslip_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    register_admin_payroll_runs__run_id__register__code__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                run_id: number;
                code: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    }[];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    cost_by_department_admin_payroll_runs__run_id__cost_by_department_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                run_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    }[];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_notices_admin_notices_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["NoticeOut"][];
                };
            };
        };
    };
    publish_admin_notices_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["NoticeCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["NoticeOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    delete_admin_notices__notice_id__delete: {
        parameters: {
            query: {
                reason: string;
            };
            header?: never;
            path: {
                notice_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    preview_admin_comms_preview_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["AudienceIn"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    messages_admin_comms_messages_get: {
        parameters: {
            query?: {
                status?: components["schemas"]["MessageStatus"] | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    }[];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    compose_admin_comms_messages_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ComposeIn"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    approve_admin_comms_messages__message_id__approve_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                message_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    broadcast_admin_comms_broadcast_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["BroadcastIn"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    cancel_admin_comms_messages__message_id__cancel_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                message_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    delivery_report_admin_comms_messages__message_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                message_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    unreachable_admin_comms_unreachable_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    }[];
                };
            };
        };
    };
    templates_admin_comms_templates_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    }[];
                };
            };
        };
    };
    supersede_template_admin_comms_templates_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["TemplateIn"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    set_preference_admin_comms_preferences_put: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["PreferenceIn"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    invoices_admin_fees_invoices_get: {
        parameters: {
            query?: {
                month?: number | null;
                year?: number | null;
                status_?: components["schemas"]["InvoiceStatus"] | null;
                class_section_id?: number | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    }[];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    generate_admin_fees_invoices_generate_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["GenerateIn"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    void_invoice_admin_fees_invoices__invoice_id__void_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                invoice_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["app__api__admin__fees__ReasonIn"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    ledger_admin_fees_ledger__student_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                student_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    collect_admin_fees_payments_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CollectIn"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    reverse_admin_fees_payments__payment_id__reverse_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                payment_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["app__api__admin__fees__ReasonIn"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    defaulters_admin_fees_defaulters_get: {
        parameters: {
            query?: {
                min_amount?: number | string;
                class_section_id?: number | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    }[];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    daybook_admin_fees_daybook_get: {
        parameters: {
            query?: {
                on?: string | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    periods_admin_fees_periods_get: {
        parameters: {
            query?: {
                year?: number | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    }[];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    close_period_admin_fees_periods__year___month__close_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                year: number;
                month: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["app__api__admin__fees__ReasonIn"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    reopen_period_admin_fees_periods__year___month__reopen_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                year: number;
                month: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["app__api__admin__fees__ReasonIn"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    collection_admin_fees_collection_get: {
        parameters: {
            query?: {
                year?: number | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    heads_admin_fees_heads_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    }[];
                };
            };
        };
    };
    create_head_admin_fees_heads_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["app__api__admin__fee_setup__HeadIn"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    plans_admin_fees_plans_get: {
        parameters: {
            query?: {
                academic_year_id?: number | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    }[];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_plan_admin_fees_plans_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["PlanIn"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    assign_plan_admin_fees_assignments_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["AssignIn"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    concessions_admin_fees_concessions_get: {
        parameters: {
            query?: {
                status_?: components["schemas"]["ConcessionStatus"] | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    }[];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    request_concession_admin_fees_concessions_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ConcessionIn"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    decide_concession_admin_fees_concessions__concession_id__decide_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                concession_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["DecideIn"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    sibling_sweep_admin_fees_concessions_sibling_sweep_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
        };
    };
    attendance_roll_admin_attendance_get: {
        parameters: {
            query: {
                class_section_id: number;
                date: string;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RollRow"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    attendance_summary_admin_attendance_summary_get: {
        parameters: {
            query?: {
                from?: string | null;
                to?: string | null;
                class_section_id?: number | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AttendanceSummary"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    absentees_admin_attendance_absentees_get: {
        parameters: {
            query?: {
                date?: string | null;
                class_section_id?: number | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    }[];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    shortage_admin_attendance_shortage_get: {
        parameters: {
            query?: {
                threshold?: number | null;
                class_section_id?: number | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    }[];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    holidays_admin_attendance_holidays_get: {
        parameters: {
            query?: {
                year?: number | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    }[];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    add_holiday_admin_attendance_holidays_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["HolidayIn"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    leave_requests_admin_attendance_leave_requests_get: {
        parameters: {
            query?: {
                status_?: components["schemas"]["LeaveStatus"] | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    }[];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    decide_admin_attendance_leave_requests__request_id__decide_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                request_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["LeaveDecision"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    periods_admin_timetable_periods_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    }[];
                };
            };
        };
    };
    add_period_admin_timetable_periods_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["PeriodIn"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    slots_admin_timetable_slots_get: {
        parameters: {
            query?: {
                class_section_id?: number | null;
                teacher_id?: number | null;
                day_of_week?: components["schemas"]["DayOfWeek"] | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    }[];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_slot_admin_timetable_slots_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["SlotIn"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    check_admin_timetable_slots_check_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["SlotIn"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_slot_admin_timetable_slots__slot_id__put: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                slot_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["SlotIn"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    delete_slot_admin_timetable_slots__slot_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                slot_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    workload_admin_timetable_workload_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
        };
    };
    completeness_admin_timetable_completeness_get: {
        parameters: {
            query?: {
                academic_year_id?: number | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    }[];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    day_plan_admin_timetable_day_get: {
        parameters: {
            query?: {
                date?: string | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    }[];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    free_teachers_admin_timetable_slots__slot_id__free_teachers_get: {
        parameters: {
            query?: {
                date?: string | null;
            };
            header?: never;
            path: {
                slot_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    }[];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    substitutions_admin_timetable_substitutions_get: {
        parameters: {
            query?: {
                date?: string | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    }[];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    arrange_admin_timetable_substitutions_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["SubstitutionIn"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    vehicles_admin_transport_vehicles_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    }[];
                };
            };
        };
    };
    add_vehicle_admin_transport_vehicles_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["VehicleIn"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    vehicle_compliance_admin_transport_vehicles__vehicle_id__compliance_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                vehicle_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    vehicle_status_admin_transport_vehicles__vehicle_id__status_patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                vehicle_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["VehicleStatusIn"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    slabs_admin_transport_slabs_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    }[];
                };
            };
        };
    };
    add_slab_admin_transport_slabs_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["SlabIn"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    routes_admin_transport_routes_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    }[];
                };
            };
        };
    };
    add_route_admin_transport_routes_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RouteIn"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    put_stops_admin_transport_routes__route_id__stops_put: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                route_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["StopIn"][];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    crew_admin_transport_routes__route_id__crew_patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                route_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CrewIn"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    route_status_admin_transport_routes__route_id__status_patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                route_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RouteStatusIn"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    roadworthiness_admin_transport_routes__route_id__roadworthiness_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                route_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    route_students_admin_transport_routes__route_id__students_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                route_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    }[];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    assign_admin_transport_assignments_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["app__api__admin__transport__AssignmentIn"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    assignment_status_admin_transport_assignments__assignment_id__patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                assignment_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["AssignmentStatusIn"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    charges_admin_transport_charges_get: {
        parameters: {
            query: {
                year: number;
                month: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    requests_admin_transport_requests_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    }[];
                };
            };
        };
    };
    expiring_admin_transport_expiring_get: {
        parameters: {
            query?: {
                within_days?: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    }[];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    read_settings_admin_configuration_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
        };
    };
    write_settings_admin_configuration_put: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["app__api__admin__settings__SettingsUpdate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_custom_fields_admin_custom_fields_get: {
        parameters: {
            query?: {
                entity?: components["schemas"]["OwnerType"];
                include_inactive?: boolean;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    }[];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_custom_field_admin_custom_fields_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CustomFieldCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    retire_custom_field_admin_custom_fields__field_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                field_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_cycles_admin_admission_cycles_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    }[];
                };
            };
        };
    };
    create_cycle_admin_admission_cycles_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CycleCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_cycle_admin_admission_cycles__cycle_id__patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                cycle_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CycleUpdate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_class_config_admin_admission_cycles__cycle_id__classes_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                cycle_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    }[];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    set_class_config_admin_admission_cycles__cycle_id__classes_put: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                cycle_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ClassConfigInput"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_enquiries_admin_admission_enquiries_get: {
        parameters: {
            query?: {
                cycle_id?: number | null;
                status?: components["schemas"]["EnquiryStatus"] | null;
                /** @description Only enquiries whose follow-up is due on or before this date */
                due_by?: string | null;
                q?: string | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    }[];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_enquiry_admin_admission_enquiries_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["EnquiryCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    enquiry_detail_admin_admission_enquiries__enquiry_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                enquiry_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    mark_invalid_admin_admission_enquiries__enquiry_id__delete: {
        parameters: {
            query: {
                reason: string;
            };
            header?: never;
            path: {
                enquiry_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    log_interaction_admin_admission_enquiries__enquiry_id__interactions_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                enquiry_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["InteractionCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    funnel_admin_admission_cycles__cycle_id__funnel_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                cycle_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_applications_admin_admission_applications_get: {
        parameters: {
            query?: {
                cycle_id?: number | null;
                status?: components["schemas"]["ApplicationStatus"] | null;
                class_applying_for?: string | null;
                category?: components["schemas"]["AdmissionCategory"] | null;
                q?: string | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    }[];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_application_admin_admission_applications_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ApplicantDetails"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    application_detail_admin_admission_applications__application_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                application_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_application_admin_admission_applications__application_id__patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                application_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ApplicationUpdate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    set_guardians_admin_admission_applications__application_id__guardians_put: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                application_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["app__api__admin__applications__GuardianInput"][];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    set_siblings_admin_admission_applications__application_id__siblings_put: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                application_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["SiblingInput"][];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    sibling_search_admin_admission_sibling_search_get: {
        parameters: {
            query: {
                q: string;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    }[];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    read_medical_admin_admission_applications__application_id__medical_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                application_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    set_medical_admin_admission_applications__application_id__medical_put: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                application_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["MedicalInput"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    submit_application_admin_admission_applications__application_id__submit_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                application_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    move_status_admin_admission_applications__application_id__status_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                application_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["StatusMove"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    verify_claims_admin_admission_applications__application_id__verify_claims_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                application_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    checklist_admin_admission_applications__application_id__documents_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                application_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    upload_document_admin_admission_applications__application_id__documents_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                application_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "multipart/form-data": components["schemas"]["Body_upload_document_admin_admission_applications__application_id__documents_post"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    download_url_admin_admission_documents__document_id__url_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                document_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    verify_document_admin_admission_documents__document_id__verify_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                document_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["Verdict"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    schedule_assessment_admin_admission_applications__application_id__assessments_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                application_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["AssessmentSchedule"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    assessment_slot_admin_admission_assessments_get: {
        parameters: {
            query?: {
                /** @description Everything scheduled at or after this moment */
                on?: string | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    }[];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    record_marks_admin_admission_assessments__assessment_id__marks_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                assessment_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["MarksInput"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    schedule_interview_admin_admission_applications__application_id__interviews_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                application_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["InterviewSchedule"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    read_interview_admin_admission_interviews__interview_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                interview_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    record_feedback_admin_admission_interviews__interview_id__feedback_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                interview_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["PanelFeedback"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    evaluation_admin_admission_applications__application_id__evaluation_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                application_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    seats_admin_admission_cycles__cycle_id__seats_get: {
        parameters: {
            query?: {
                class_name?: string | null;
            };
            header?: never;
            path: {
                cycle_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    }[];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    merit_admin_admission_cycles__cycle_id__merit_get: {
        parameters: {
            query: {
                class_name: string;
            };
            header?: never;
            path: {
                cycle_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    decide_admin_admission_applications__application_id__decision_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                application_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["DecisionInput"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    decide_batch_admin_admission_cycles__cycle_id__decisions_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                cycle_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["BatchDecision"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    issue_offer_admin_admission_applications__application_id__offer_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                application_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["OfferInput"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    respond_admin_admission_applications__application_id__offer_response_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                application_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["OfferResponse"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    waitlist_admin_admission_cycles__cycle_id__waitlist_get: {
        parameters: {
            query: {
                class_name: string;
            };
            header?: never;
            path: {
                cycle_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    }[];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    promote_admin_admission_cycles__cycle_id__waitlist_promote_post: {
        parameters: {
            query: {
                class_name: string;
            };
            header?: never;
            path: {
                cycle_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    decision_history_admin_admission_applications__application_id__decisions_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                application_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    }[];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_payments_admin_admission_applications__application_id__payments_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                application_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    }[];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    collect_payment_admin_admission_applications__application_id__payments_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                application_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["PaymentInput"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    void_payment_admin_admission_payments__payment_id__delete: {
        parameters: {
            query: {
                reason: string;
            };
            header?: never;
            path: {
                payment_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    conversion_preview_admin_admission_applications__application_id__conversion_preview_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                application_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    convert_admin_admission_applications__application_id__convert_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                application_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    dashboard_admin_admission_cycles__cycle_id__dashboard_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                cycle_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    reports_admin_admission_cycles__cycle_id__reports_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                cycle_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    library_admin_reports_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
        };
    };
    run_admin_reports__code__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                code: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    export_admin_reports__code__export_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                code: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    dashboard_teacher_dashboard_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
        };
    };
    my_classes_teacher_classes_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    }[];
                };
            };
        };
    };
    class_roster_teacher_classes__class_section_id__students_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                class_section_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    }[];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    my_timetable_teacher_timetable_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SlotOut"][];
                };
            };
        };
    };
    my_profile_teacher_profile_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
        };
    };
    my_subjects_teacher_subjects_get: {
        parameters: {
            query?: {
                class_section_id?: number | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    }[];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    roll_sheet_teacher_attendance_get: {
        parameters: {
            query: {
                class_section_id: number;
                date: string;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RollRow"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    mark_teacher_attendance_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["AttendanceMarkRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RollRow"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_homework_teacher_homework_get: {
        parameters: {
            query?: {
                class_section_id?: number | null;
                subject_id?: number | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HomeworkOut"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_teacher_homework_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["HomeworkCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HomeworkOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    delete_teacher_homework__homework_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                homework_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_teacher_homework__homework_id__patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                homework_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["HomeworkUpdate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HomeworkOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    submissions_teacher_homework__homework_id__submissions_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                homework_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SubmissionRow"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    my_papers_teacher_exams_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ExamScheduleOut"][];
                };
            };
        };
    };
    roster_teacher_marks_get: {
        parameters: {
            query: {
                exam_schedule_id: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MarksRosterRow"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    enter_teacher_marks_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["MarksRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MarksRosterRow"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    mine_teacher_announcements_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["NoticeOut"][];
                };
            };
        };
    };
    publish_teacher_announcements_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["AnnouncementCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["NoticeOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    dashboard_student_dashboard_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
        };
    };
    timetable_student_timetable_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SlotOut"][];
                };
            };
        };
    };
    profile_student_profile_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
        };
    };
    my_notices_student_notices_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown[];
                };
            };
        };
    };
    my_attendance_student_attendance_get: {
        parameters: {
            query?: {
                month?: number | null;
                year?: number | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AttendanceMonth"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    my_homework_student_homework_get: {
        parameters: {
            query?: {
                status?: string;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["StudentHomeworkOut"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    submit_student_homework__homework_id__submit_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                homework_id: number;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["SubmitRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["StudentHomeworkOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    upcoming_exams_student_exams_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ExamScheduleOut"][];
                };
            };
        };
    };
    my_results_student_results_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    }[];
                };
            };
        };
    };
    report_card_student_results__exam_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                exam_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ReportCard"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    children_parent_children_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    }[];
                };
            };
        };
    };
    summary_parent_children__student_id__summary_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                student_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    child_attendance_parent_children__student_id__attendance_get: {
        parameters: {
            query?: {
                month?: number | null;
                year?: number | null;
            };
            header?: never;
            path: {
                student_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AttendanceMonth"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    child_homework_parent_children__student_id__homework_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                student_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["StudentHomeworkOut"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    child_results_parent_children__student_id__results_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                student_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    }[];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    child_report_card_parent_children__student_id__results__exam_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                student_id: number;
                exam_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ReportCard"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    child_profile_parent_children__student_id__profile_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                student_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    my_profile_parent_profile_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
        };
    };
    my_notices_parent_notices_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown[];
                };
            };
        };
    };
    my_leave_requests_parent_leave_requests_get: {
        parameters: {
            query: {
                student_id: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    }[];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    apply_for_leave_parent_leave_requests_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["LeaveIn"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    child_transport_parent_children__student_id__transport_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                student_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    } | null;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    invoices_parent_fees_get: {
        parameters: {
            query?: {
                student_id?: number | null;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    }[];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    ledger_parent_fees_ledger_get: {
        parameters: {
            query: {
                student_id: number;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    pay_parent_fees_pay_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["PayIn"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    receipt_parent_fees_receipts__payment_id__pdf_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                payment_id: number;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    open_cycle_public__school_code__admission_open_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                school_code: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    apply_public__school_code__admission_apply_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                school_code: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["PublicApplication"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    application_status_public__school_code__admission_status_get: {
        parameters: {
            query: {
                application_no: string;
                date_of_birth: string;
            };
            header?: never;
            path: {
                school_code: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: unknown;
                    };
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    health_health_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: string;
                    };
                };
            };
        };
    };
}
