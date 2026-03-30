from __future__ import annotations

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, render_template_string, request, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
UPLOADS_DIR = BASE_DIR / "uploads"
DATA_FILE = DATA_DIR / "storage.json"
ADMIN_CODE = "111@95"

DATA_DIR.mkdir(exist_ok=True)
UPLOADS_DIR.mkdir(exist_ok=True)

DEFAULT_STATE: dict[str, Any] = {
    "page_visits": 0,
    "main_sections": [
        {"id": "admin", "title": "الإدارة (خاص بإدارة المدرسة)", "icon": "🔐", "desc": "قسم خاص بإدارة المدرسة لإدارة الملفات ورفع محتوى HTML وتحديثه بشكل آمن.", "admin_only": True, "children": []},
        {
            "id": "lrc",
            "title": "مركز مصادر التعلّم",
            "icon": "📖",
            "desc": "بين صفحات الكتب، حصص مكتبية، مهارات الوعي المعلوماتي، البحث العلمي، التقانة.",
            "children": [
                {"id": "library-corridors", "title": "بين أروقة المكتبة", "icon": "📚", "desc": "رحلة أسبوعية في عالم الكتب.", "weekly_book": {"title": "كتاب الأسبوع", "description": "أضيفي هنا نبذة مختصرة عن الكتاب المختار لهذا الأسبوع.", "quote": "في المكتبة تبدأ رحلة المعرفة، وبالقراءة تُبنى العقول.", "image": ""}},
                {"id": "books-pages", "title": "بين صفحات الكتب", "icon": "📚", "desc": "عروض كتب، ملخصات، تشجيع القراءة، وأنشطة معرفية."},
                {"id": "library-lessons", "title": "حصص مكتبية", "icon": "🪑", "desc": "حصص المكتبة، أنشطة المركز، والبرامج التفاعلية."},
                {"id": "info-awareness", "title": "مهارات الوعي المعلوماتي", "icon": "🧠", "desc": "البحث، التحقق، التقييم، وأخلاقيات المعلومات."},
                {"id": "research", "title": "البحث العلمي", "icon": "🔬", "desc": "خطوات البحث، التوثيق، التقارير، والمشاريع البحثية."},
                {"id": "tech", "title": "التقانة", "icon": "💻", "desc": "الأدوات الرقمية، التطبيقات التعليمية، والتقنيات الحديثة."}
            ]
        },
        {"id": "guidance", "title": "الإرشاد النفسي والاجتماعي", "icon": "🧠", "desc": "محتوى إرشادي وتوعوي داعم للطالبات.", "children": []},
        {"id": "activities", "title": "الأنشطة المدرسية", "icon": "🎯", "desc": "فعاليات ومسابقات وأنشطة مدرسية متنوعة.", "children": []},
        {"id": "health", "title": "الصحة والطب", "icon": "🩺", "desc": "محتوى صحي وتثقيف طبي وإرشادات وقائية.", "children": []},
        {"id": "safety", "title": "الأمن والسلامة", "icon": "🛡", "desc": "السلامة المدرسية وخطط الإخلاء والإرشادات.", "children": []},
        {"id": "ai", "title": "التقنية والذكاء الاصطناعي", "icon": "🤖", "desc": "أدوات تقنية حديثة وموارد التعلم الذكي.", "children": []},
        {"id": "teachers", "title": "المعلمات", "icon": "📘", "desc": "ملفات الدعم المهني والمحتوى التعليمي للمعلمات.", "children": []},
        {"id": "mothers", "title": "الأمهات", "icon": "👩‍👧", "desc": "موارد توعوية وداعمة للتواصل والتوجيه.", "children": []},
        {"id": "aljuman", "title": "قاعة الجمان", "icon": "🏛", "desc": "فعاليات ومواد خاصة بقاعة الجمان.", "children": []}
    ],
    "subjects": [
        {"id": "islamic", "title": "التربية الإسلامية", "icon": "🕌", "desc": "محتوى التربية الإسلامية من الخامس إلى الثاني عشر.", "grades": ["ديني قيمي الصف الخامس", "ديني قيمي الصف السادس", "ديني قيمي الصف السابع", "ديني قيمي الصف الثامن", "التربية الإسلامية الصف التاسع", "التربية الإسلامية الصف العاشر", "التربية الإسلامية الصف الحادي عشر", "التربية الإسلامية الصف الثاني عشر"]},
        {"id": "arabic", "title": "اللغة العربية", "icon": "📝", "desc": "لغتي الجميلة والمؤنس والمفيد.", "grades": ["لغتي الجميلة الصف الخامس", "لغتي الجميلة الصف السادس", "لغتي الجميلة الصف السابع", "لغتي الجميلة الصف الثامن", "لغتي الجميلة الصف التاسع", "لغتي الجميلة الصف العاشر", "المؤنس والمفيد الصف الحادي عشر", "المؤنس والمفيد الصف الثاني عشر"]},
        {"id": "english", "title": "اللغة الإنجليزية", "icon": "🇬🇧", "desc": "محتوى اللغة الإنجليزية لجميع الصفوف.", "grades": ["اللغة الإنجليزية الصف الخامس", "اللغة الإنجليزية الصف السادس", "اللغة الإنجليزية الصف السابع", "اللغة الإنجليزية الصف الثامن", "اللغة الإنجليزية الصف التاسع", "اللغة الإنجليزية الصف العاشر", "اللغة الإنجليزية الصف الحادي عشر", "اللغة الإنجليزية الصف الثاني عشر"]},
        {"id": "science", "title": "العلوم", "icon": "🔬", "desc": "علوم، كيمياء، فيزياء، أحياء، علوم بيئية.", "grades": ["العلوم الصف الخامس", "العلوم الصف السادس", "العلوم الصف السابع", "العلوم الصف الثامن", "الكيمياء الصف التاسع", "الكيمياء الصف العاشر", "الكيمياء الصف الحادي عشر", "الكيمياء الصف الثاني عشر", "الفيزياء الصف التاسع", "الفيزياء الصف العاشر", "الفيزياء الصف الحادي عشر", "الفيزياء الصف الثاني عشر", "الأحياء الصف التاسع", "الأحياء الصف العاشر", "الأحياء الصف الحادي عشر", "الأحياء الصف الثاني عشر", "العلوم البيئية الصف الحادي عشر", "العلوم البيئية الصف الثاني عشر"]},
        {"id": "math", "title": "الرياضيات", "icon": "📐", "desc": "الرياضيات الأساسية والمتقدمة حسب الصفوف.", "grades": ["الرياضيات الصف الخامس", "الرياضيات الصف السادس", "الرياضيات الصف السابع", "الرياضيات الصف الثامن", "الرياضيات الصف التاسع", "الرياضيات الصف العاشر", "الرياضيات الأساسية الصف الحادي عشر", "الرياضيات المتقدمة الصف الحادي عشر", "الرياضيات الأساسية الصف الثاني عشر", "الرياضيات المتقدمة الصف الثاني عشر"]},
        {"id": "social", "title": "الدراسات الاجتماعية", "icon": "🌍", "desc": "هذا وطني والجغرافيا والتقنيات الحديثة.", "grades": ["الدراسات الاجتماعية الصف الخامس", "الدراسات الاجتماعية الصف السادس", "الدراسات الاجتماعية الصف السابع", "الدراسات الاجتماعية الصف الثامن", "الدراسات الاجتماعية الصف التاسع", "الدراسات الاجتماعية الصف العاشر", "هذا وطني الصف الحادي عشر", "هذا وطني الصف الثاني عشر", "الجغرافيا والتقنيات الحديثة الصف الثاني عشر", "العالم من حولي الصف الثاني عشر"]},
        {"id": "it", "title": "تقنية المعلومات", "icon": "💾", "desc": "من الصف الخامس إلى الصف العاشر.", "grades": ["تقنية المعلومات الصف الخامس", "تقنية المعلومات الصف السادس", "تقنية المعلومات الصف السابع", "تقنية المعلومات الصف الثامن", "تقنية المعلومات الصف التاسع", "تقنية المعلومات الصف العاشر"]},
        {"id": "life", "title": "المهارات الحياتية", "icon": "🌱", "desc": "من الصف الخامس إلى الصف العاشر.", "grades": ["المهارات الحياتية الصف الخامس", "المهارات الحياتية الصف السادس", "المهارات الحياتية الصف السابع", "المهارات الحياتية الصف الثامن", "المهارات الحياتية الصف التاسع", "المهارات الحياتية الصف العاشر"]},
        {"id": "sports", "title": "الرياضة المدرسية", "icon": "🏃", "desc": "محتوى الرياضة المدرسية لجميع الصفوف المعتمدة.", "grades": ["الرياضة المدرسية الصف الخامس", "الرياضة المدرسية الصف السادس", "الرياضة المدرسية الصف السابع", "الرياضة المدرسية الصف الثامن", "الرياضة المدرسية الصف التاسع", "الرياضة المدرسية الصف العاشر", "الرياضة المدرسية الصف الحادي عشر", "الرياضة المدرسية الصف الثاني عشر"]},
        {"id": "music", "title": "المهارات الموسيقية", "icon": "🎵", "desc": "الموسيقى للصفوف المعتمدة.", "grades": ["الموسيقى الصف الخامس", "الموسيقى الصف السادس", "الموسيقى الصف السابع", "الموسيقى الصف الثامن", "الموسيقى الصف التاسع", "الموسيقى الصف العاشر", "الموسيقى الصف الحادي عشر", "الموسيقى الصف الثاني عشر"]},
        {"id": "arts", "title": "الفنون التشكيلية", "icon": "🎨", "desc": "محتوى الفنون التشكيلية لجميع الصفوف.", "grades": ["الفنون التشكيلية الصف الخامس", "الفنون التشكيلية الصف السادس", "الفنون التشكيلية الصف السابع", "الفنون التشكيلية الصف الثامن", "الفنون التشكيلية الصف التاسع", "الفنون التشكيلية الصف العاشر", "الفنون التشكيلية الصف الحادي عشر", "الفنون التشكيلية الصف الثاني عشر"]},
        {"id": "career", "title": "مسارك المهني", "icon": "🧭", "desc": "مادة مستقلة للصفين الحادي عشر والثاني عشر.", "grades": ["مسارك المهني الصف الحادي عشر", "مسارك المهني الصف الثاني عشر"]}
    ],
    "paths": {},
    "section_visits": {},
    "path_opens": {},
    "likes_by_visitor": {}
}

INDEX_HTML = r'''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>منصة المكتبة الرقمية التفاعلية</title>
  <style>
    :root {
      --bg1:#eef8ff;--bg2:#f7fcff;--primary:#1367f2;--primary2:#3fc8ff;--violet:#8367ff;
      --deep:#12304d;--muted:#617792;--danger:#d84c4c;--glass:rgba(255,255,255,.7);
      --border:rgba(255,255,255,.45);--shadow:0 14px 32px rgba(20,76,149,.14);
    }
    *{box-sizing:border-box} html{scroll-behavior:smooth}
    body{margin:0;font-family:Tahoma,Arial,sans-serif;color:var(--deep);background:
      radial-gradient(circle at 8% 16%,rgba(63,200,255,.22),transparent 24%),
      radial-gradient(circle at 88% 18%,rgba(131,103,255,.18),transparent 22%),
      radial-gradient(circle at 50% 82%,rgba(19,103,242,.12),transparent 28%),
      linear-gradient(135deg,var(--bg1),var(--bg2));min-height:100vh;overflow-x:hidden;position:relative}
    body::before{content:"";position:fixed;inset:0;background-image:
      linear-gradient(rgba(19,103,242,.04) 1px,transparent 1px),
      linear-gradient(90deg,rgba(19,103,242,.04) 1px,transparent 1px);
      background-size:34px 34px;pointer-events:none;z-index:-2}
    .float-shape{position:fixed;z-index:-1;opacity:.08;user-select:none;pointer-events:none;animation:floatUp 8s ease-in-out infinite;font-size:4.8rem}
    .shape-book{top:14%;left:3%}.shape-ai{bottom:12%;right:4%;animation-delay:1.5s}.shape-chip{top:58%;left:7%;animation-delay:2.4s}
    @keyframes floatUp{0%,100%{transform:translateY(0) rotate(0deg)}50%{transform:translateY(-16px) rotate(4deg)}}
    .topbar{position:sticky;top:0;z-index:20;background:rgba(9,37,83,.84);color:#fff;text-align:center;padding:12px 14px;font-weight:800;backdrop-filter:blur(14px);box-shadow:0 10px 25px rgba(9,37,83,.18)}
    .oman-link{position:fixed;left:14px;top:110px;z-index:19;display:flex;align-items:center;gap:10px;padding:12px 16px;border-radius:18px;background:linear-gradient(135deg,rgba(19,103,242,.95),rgba(63,200,255,.92));color:#fff;text-decoration:none;font-weight:900;box-shadow:0 12px 24px rgba(19,103,242,.24);border:1px solid rgba(255,255,255,.28);backdrop-filter:blur(12px);max-width:240px;line-height:1.6;transition:.2s ease}.oman-link:hover{transform:translateY(-3px)}
    .wrapper{width:min(1420px,calc(100% - 28px));margin:0 auto;padding:18px 0 34px}
    .hero{position:relative;border-radius:28px;padding:32px 24px;text-align:center;background:linear-gradient(135deg,rgba(255,255,255,.78),rgba(255,255,255,.6));border:1px solid var(--border);backdrop-filter:blur(18px);box-shadow:var(--shadow);overflow:hidden}
    .hero::before,.hero::after{content:"";position:absolute;border-radius:50%;pointer-events:none}
    .hero::before{width:260px;height:260px;top:-90px;right:-50px;background:radial-gradient(circle,rgba(63,200,255,.23),transparent 65%)}
    .hero::after{width:230px;height:230px;bottom:-80px;left:-40px;background:radial-gradient(circle,rgba(131,103,255,.18),transparent 68%)}
    .hero-badge{display:inline-flex;align-items:center;gap:8px;padding:10px 18px;border-radius:999px;background:rgba(255,255,255,.82);color:var(--primary);font-weight:800;margin-bottom:14px;box-shadow:0 8px 18px rgba(19,103,242,.1)}
    .hero h1,.hero h2,.hero h3,.hero p{margin:0;position:relative;z-index:1}.hero h1{font-size:clamp(1.6rem,2.8vw,2.4rem);margin-bottom:10px}.hero h2{font-size:clamp(1.25rem,2.2vw,1.95rem);color:var(--primary);margin-bottom:8px}.hero h3{font-size:clamp(1.15rem,1.95vw,1.65rem);color:var(--violet);margin-bottom:12px}.hero p{color:var(--muted);font-weight:800}
    .quick-stats{margin-top:20px;display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px;position:relative;z-index:1}
    .q-card{background:rgba(255,255,255,.76);border:1px solid rgba(255,255,255,.6);border-radius:20px;padding:16px;box-shadow:0 10px 20px rgba(19,103,242,.08)}
    .q-card .label{color:var(--muted);font-weight:700;font-size:.94rem}.q-card .value{margin-top:8px;font-size:1.55rem;color:var(--primary);font-weight:900}
    .section{margin-top:26px;border-radius:26px;padding:22px;background:rgba(255,255,255,.58);border:1px solid rgba(255,255,255,.45);backdrop-filter:blur(16px);box-shadow:var(--shadow)}
    .section-head{display:flex;justify-content:space-between;gap:12px;align-items:center;flex-wrap:wrap;margin-bottom:16px}
    .section-title{font-size:1.35rem;font-weight:900;display:flex;align-items:center;gap:10px}.section-subtitle{color:var(--muted);font-weight:700;font-size:.95rem;margin-top:6px}
    .actions-inline{display:flex;gap:8px;flex-wrap:wrap;align-items:center}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px}
    .card{position:relative;border-radius:22px;background:linear-gradient(180deg,rgba(255,255,255,.86),rgba(255,255,255,.7));border:1px solid rgba(255,255,255,.65);padding:18px;box-shadow:0 12px 24px rgba(19,103,242,.08);min-height:175px;overflow:hidden;transition:transform .22s ease,box-shadow .22s ease;cursor:pointer}
    .card:hover{transform:translateY(-6px);box-shadow:0 18px 30px rgba(19,103,242,.15)}
    .card::after{content:"";position:absolute;width:125px;height:125px;border-radius:50%;left:-30px;bottom:-52px;background:radial-gradient(circle,rgba(63,200,255,.2),transparent 68%);pointer-events:none}
    .card-top{display:flex;justify-content:space-between;gap:10px;align-items:flex-start;position:relative;z-index:1}.card-icon{width:58px;height:58px;border-radius:18px;display:flex;align-items:center;justify-content:center;font-size:2rem;background:linear-gradient(135deg,rgba(19,103,242,.14),rgba(63,200,255,.18));box-shadow:inset 0 0 0 1px rgba(19,103,242,.08);flex-shrink:0}
    .card-title-wrap{flex:1}.card-title-wrap h4{margin:0 0 8px;font-size:1.05rem}.card-title-wrap p{margin:0;color:var(--muted);line-height:1.75;font-size:.92rem;font-weight:700}.card-tools{display:flex;gap:6px;flex-wrap:wrap;align-items:center}
    .mini-btn,.btn{border:none;border-radius:14px;padding:10px 15px;font-weight:800;font-family:inherit;cursor:pointer;display:inline-flex;align-items:center;justify-content:center;gap:8px;transition:.2s ease;text-decoration:none}.mini-btn{width:34px;height:34px;padding:0;border-radius:12px;background:rgba(255,255,255,.88);border:1px solid rgba(19,103,242,.08);font-size:.95rem}
    .btn-primary{color:#fff;background:linear-gradient(135deg,var(--primary),var(--primary2));box-shadow:0 10px 20px rgba(19,103,242,.22)}.btn-light{background:rgba(255,255,255,.88);color:var(--deep);border:1px solid rgba(19,103,242,.08)}.btn-danger{background:rgba(216,76,76,.11);color:var(--danger);border:1px solid rgba(216,76,76,.18)}.btn-like.active{background:rgba(255,217,90,.24);color:#8a6500;border:1px solid rgba(211,139,0,.24)}
    .toolbar{display:flex;justify-content:space-between;flex-wrap:wrap;gap:10px;align-items:center;padding:14px 16px;border-radius:20px;background:rgba(255,255,255,.72);border:1px solid rgba(255,255,255,.58);margin-bottom:16px;box-shadow:0 10px 20px rgba(19,103,242,.08)}.breadcrumb{color:var(--primary);font-weight:900}.muted{color:var(--muted);font-weight:700}.view{display:none;margin-top:22px}.view.active{display:block}
    .file-list{display:grid;gap:14px}.weekly-book-card{display:grid;grid-template-columns:220px 1fr;gap:18px;align-items:center;border-radius:24px;padding:18px;background:linear-gradient(135deg,rgba(255,255,255,.9),rgba(255,255,255,.72));border:1px solid rgba(255,255,255,.7);box-shadow:0 12px 26px rgba(19,103,242,.1);margin-bottom:18px}.weekly-book-cover{height:260px;border-radius:20px;background:linear-gradient(135deg,rgba(19,103,242,.14),rgba(63,200,255,.18));display:flex;align-items:center;justify-content:center;font-size:4rem;color:var(--primary);overflow:hidden}.weekly-book-cover img{width:100%;height:100%;object-fit:cover;display:block}.weekly-book-meta h4{margin:0 0 10px;font-size:1.4rem}.weekly-book-badge{display:inline-block;padding:8px 14px;border-radius:999px;background:rgba(19,103,242,.1);color:var(--primary);font-weight:900;margin-bottom:10px}.weekly-book-meta p{margin:0 0 10px;line-height:1.9;color:var(--muted);font-weight:700}.weekly-book-quote{padding:12px 14px;border-radius:16px;background:rgba(131,103,255,.08);color:#4c4286;font-weight:800}@media (max-width:900px){.weekly-book-card{grid-template-columns:1fr}.weekly-book-cover{height:220px}}.file-card{display:grid;grid-template-columns:1fr auto;gap:14px;align-items:start;border-radius:22px;padding:16px;background:linear-gradient(180deg,rgba(255,255,255,.87),rgba(255,255,255,.72));border:1px solid rgba(255,255,255,.65);box-shadow:0 10px 22px rgba(19,103,242,.08)}.file-card h5{margin:0 0 8px;font-size:1.04rem}.date{color:var(--muted);font-size:.92rem;font-weight:700;margin-bottom:10px}.file-stats{display:flex;flex-wrap:wrap;gap:10px;color:var(--muted);font-size:.92rem;font-weight:800}.file-actions{display:flex;gap:8px;flex-wrap:wrap;justify-content:flex-end}
    .stats-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px}.stat-card{border-radius:22px;padding:18px;background:linear-gradient(135deg,rgba(255,255,255,.88),rgba(255,255,255,.68));border:1px solid rgba(255,255,255,.64);box-shadow:0 10px 20px rgba(19,103,242,.08)}.stat-card h5{margin:0 0 10px;color:var(--muted);font-size:1rem}.stat-card .big{font-size:1.8rem;font-weight:900;color:var(--primary)}.stat-card .small{margin-top:8px;line-height:1.75;color:var(--muted);font-weight:700}
    .footer{margin:28px 0 10px;text-align:center;padding:22px;border-radius:24px;background:linear-gradient(135deg,rgba(8,42,95,.94),rgba(56,110,205,.92));color:#fff;line-height:2;font-weight:900;box-shadow:0 14px 30px rgba(8,42,95,.22)}
    .empty{padding:24px;text-align:center;color:var(--muted);font-weight:800;border-radius:18px;background:rgba(255,255,255,.68);border:1px dashed rgba(19,103,242,.18)}
    .toast{position:fixed;left:50%;bottom:24px;transform:translateX(-50%) translateY(16px);background:rgba(7,30,71,.94);color:#fff;padding:12px 18px;border-radius:14px;font-weight:800;opacity:0;pointer-events:none;transition:.25s ease;z-index:100;box-shadow:0 10px 24px rgba(0,0,0,.18)}.toast.show{opacity:1;transform:translateX(-50%) translateY(0)}
    .modal-overlay{position:fixed;inset:0;background:rgba(7,24,54,.52);display:none;align-items:center;justify-content:center;padding:18px;z-index:50}.modal-overlay.active{display:flex}.modal{width:min(480px,100%);border-radius:24px;padding:22px;background:rgba(255,255,255,.97);box-shadow:0 24px 40px rgba(7,24,54,.24);border:1px solid rgba(255,255,255,.75)}.modal h3{margin:0 0 8px}.modal p{margin:0 0 14px;color:var(--muted);line-height:1.8;font-weight:700}.input,.file-input{width:100%;padding:12px 14px;border-radius:14px;border:1px solid rgba(19,103,242,.16);font-size:1rem;font-family:inherit;margin-bottom:12px;background:#fff}.modal-actions{display:flex;justify-content:flex-end;gap:10px;flex-wrap:wrap;margin-top:8px}
    @media (max-width:900px){.file-card{grid-template-columns:1fr}.file-actions{justify-content:flex-start}} @media (max-width:640px){.wrapper{width:min(100% - 18px,100%)}.hero{padding:24px 16px}.section{padding:18px}.card{min-height:auto}.oman-link{left:10px;right:10px;top:64px;max-width:none;justify-content:center}}
  </style>
</head>
<body>
  <div class="float-shape shape-book">📚</div><div class="float-shape shape-ai">🤖</div><div class="float-shape shape-chip">💠</div>
  <div class="topbar" id="topBar">جاري تحديث الوقت...</div>
  <a class="oman-link" href="https://ict.moe.gov.om/book/" target="_blank" rel="noopener noreferrer" title="المناهج العمانية">
    <span>📚</span>
    <span>المناهج العُمانية</span>
  </a>
  <div class="wrapper">
    <header class="hero">
      <div style="margin:16px auto 0; max-width:700px; position:relative; z-index:2;">
        <input id="searchInput" type="text" placeholder="🔍 ابحثي في المكتبة الرقمية..." style="width:100%; padding:14px 18px; border-radius:20px; border:1px solid rgba(19,103,242,0.2); outline:none; font-size:1rem; font-weight:700; box-shadow:0 8px 18px rgba(19,103,242,0.1);" />
      </div>
      <div class="hero-badge">📘 مكتبة ذكية • ذكاء اصطناعي • تعلم تفاعلي</div>
      <h1>مدرسة سلمى بنت قيس للتعليم الأساسي (5–12)</h1>
      <h2>مركز مصادر التعلّم</h2>
      <h3>المكتبة الرقمية التفاعلية</h3>
      <p>منصة رقمية تفاعلية لمحتوى تعليمي أكثر إلهامًا وتميزًا</p>
      <div class="quick-stats">
        <div class="q-card"><div class="label">عدد زوار الصفحة</div><div class="value" id="visitsCount">0</div></div>
        <div class="q-card"><div class="label">إجمالي المشاهدات</div><div class="value" id="viewsCount">0</div></div>
        <div class="q-card"><div class="label">إجمالي الإعجابات</div><div class="value" id="likesCount">0</div></div>
        <div class="q-card"><div class="label">إجمالي الملفات</div><div class="value" id="filesCount">0</div></div>
      </div>
    </header>

    <section class="section" id="sectionsArea">
      <div class="section-head">
        <div><div class="section-title">✨ الأقسام الرئيسية</div><div class="section-subtitle">بطاقات رئيسية قابلة للإدارة مع إضافة أو حذف قسم برمز سري.</div></div>
        <div class="actions-inline"><button class="btn btn-primary" id="addMainSectionBtn">➕ إضافة قسم</button></div>
      </div>
      <div class="grid" id="mainSectionsGrid"></div>
    </section>

    <section class="section" id="subjectsArea">
      <div class="section-head">
        <div><div class="section-title">📚 المواد الدراسية</div><div class="section-subtitle">المواد الدراسية المعتمدة مع إمكانية إضافة مادة أو حذفها وإدارة الصفوف داخلها.</div></div>
        <div class="actions-inline"><button class="btn btn-primary" id="addSubjectBtn">➕ إضافة مادة</button></div>
      </div>
      <div class="grid" id="subjectsGrid"></div>
    </section>

    <section class="section view" id="subView">
      <div class="toolbar">
        <div class="actions-inline"><button class="btn btn-light" id="backFromSubBtn">⬅ العودة</button><div class="breadcrumb" id="subBreadcrumb"></div></div>
        <div class="actions-inline" id="subToolbarActions"></div>
      </div>
      <div class="grid" id="subGrid"></div>
    </section>

    <section class="section view" id="filesView">
      <div class="toolbar">
        <div class="actions-inline"><button class="btn btn-light" id="backFromFilesBtn">⬅ العودة</button><div class="breadcrumb" id="filesBreadcrumb"></div></div>
        <div class="actions-inline"><button class="btn btn-primary" id="addFileBtn">➕ إضافة ملف HTML</button></div>
      </div>
      <div class="file-list" id="filesList"></div>
    </section>

    <section class="section" id="statsArea">
      <div class="section-head">
        <div>
          <div class="section-title">📊 إحصائيات الاستخدام</div>
          <div class="section-subtitle">عرض لحركة الزوار والمشاهدات والإعجابات وأكثر العناصر نشاطًا.</div>
        </div>
      </div>
      <div class="stats-grid" id="statsGrid"></div>

      <!-- الرسوم البيانية -->
      <div style="margin-top:20px; display:grid; gap:20px;">
        <canvas id="viewsChart"></canvas>
        <canvas id="sectionsChart"></canvas>
      </div>
    </section>

    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

    <footer class="footer"><div>تصميم وبرمجة وإعداد</div><div>أخصائية مركز مصادر التعلّم</div><div>الأستاذة سامية المقبالية</div></footer>
  </div>

  <div class="modal-overlay" id="modalOverlay"><div class="modal" id="modalBox"></div></div>
  <div class="toast" id="toast"></div>

  <script>
    const ADMIN_CODE = '111@95';
    let state = null;
    let ui = { level:'home', currentType:null, currentId:null, currentTitle:'', currentParentId:null };
    const topBar = document.getElementById('topBar');
    const mainSectionsGrid = document.getElementById('mainSectionsGrid');
    const subjectsGrid = document.getElementById('subjectsGrid');
    const subView = document.getElementById('subView');
    const subGrid = document.getElementById('subGrid');
    const subBreadcrumb = document.getElementById('subBreadcrumb');
    const subToolbarActions = document.getElementById('subToolbarActions');
    const filesView = document.getElementById('filesView');
    const filesList = document.getElementById('filesList');
    const filesBreadcrumb = document.getElementById('filesBreadcrumb');
    const statsGrid = document.getElementById('statsGrid');
    const modalOverlay = document.getElementById('modalOverlay');
    const modalBox = document.getElementById('modalBox');
    const toast = document.getElementById('toast');

    document.getElementById('addMainSectionBtn').addEventListener('click', () => guardedAction(openAddMainSectionModal));
    document.getElementById('addSubjectBtn').addEventListener('click', () => guardedAction(openAddSubjectModal));
    document.getElementById('backFromSubBtn').addEventListener('click', () => { subView.classList.remove('active'); ui.level='home'; window.scrollTo({top:0,behavior:'smooth'}); });
    document.getElementById('backFromFilesBtn').addEventListener('click', () => {
      filesView.classList.remove('active');
      if (ui.currentType === 'main-child') {
        const parent = state.main_sections.find(s => s.id === ui.currentParentId);
        if (parent) openMainSection(parent, false);
      } else if (ui.currentType === 'subject-grade') {
        const subject = state.subjects.find(s => s.id === ui.currentParentId);
        if (subject) openSubject(subject, false);
      }
    });
    document.getElementById('addFileBtn').addEventListener('click', () => guardedAction(openAddFileModal));
    modalOverlay.addEventListener('click', e => { if (e.target === modalOverlay) closeModal(); });

    init();
    attachSearch();
    renderClock();
    setInterval(renderClock, 1000);

    async function init(){ await fetchState(); renderAll(); }
    async function fetchState(){ const res = await fetch('/api/state'); state = await res.json(); }

    function renderClock(){
      const now = new Date();
      const days = ['الأحد','الاثنين','الثلاثاء','الأربعاء','الخميس','الجمعة','السبت'];
      const months = ['يناير','فبراير','مارس','أبريل','مايو','يونيو','يوليو','أغسطس','سبتمبر','أكتوبر','نوفمبر','ديسمبر'];
      let hours = now.getHours(); const ampm = hours >= 12 ? 'مساءً' : 'صباحًا'; hours = hours % 12 || 12;
      const minutes = String(now.getMinutes()).padStart(2,'0'); const seconds = String(now.getSeconds()).padStart(2,'0');
      topBar.textContent = `${days[now.getDay()]} | ${now.getDate()} ${months[now.getMonth()]} ${now.getFullYear()} | ${hours}:${minutes}:${seconds} ${ampm}`;
    }

    function renderAll(){ renderMainSections(); renderSubjects(); renderStats(); renderCharts(); updateQuickCounters(); }
    function renderMainSections(){ mainSectionsGrid.innerHTML=''; state.main_sections.forEach(section => mainSectionsGrid.appendChild(createItemCard(section,'main'))); }
    function renderSubjects(){ subjectsGrid.innerHTML=''; state.subjects.forEach(subject => subjectsGrid.appendChild(createItemCard(subject,'subject'))); }

    function createItemCard(item,type){
      const card = document.createElement('div'); card.className='card';
      card.innerHTML = `<div class="card-top"><div class="card-icon">${item.icon || '📁'}</div><div class="card-tools"><button class="mini-btn add" title="إضافة">➕</button><button class="mini-btn del" title="حذف">🗑</button></div></div><div class="card-title-wrap"><h4>${escapeHtml(item.title)}</h4><p>${escapeHtml(item.desc || 'فتح المحتوى')}</p></div>`;
      card.addEventListener('click', e => {
        if (e.target.closest('.mini-btn')) return;
        if (type === 'main') { if (item.admin_only) guardedAction(() => openMainSection(item,true)); else openMainSection(item,true); }
        if (type === 'subject') openSubject(item,true);
        if (type === 'main-child') openFiles('main-child', item.parentId, item.id, item.title, item.breadcrumb);
        if (type === 'subject-grade') openFiles('subject-grade', item.parentId, item.id, item.title, item.breadcrumb);
      });
      const addBtn = card.querySelector('.add'); const delBtn = card.querySelector('.del');
      if (type === 'main') {
        addBtn.title = 'إضافة قسم فرعي';
        addBtn.addEventListener('click', e => { e.stopPropagation(); guardedAction(() => openAddMainChildModal(item.id)); });
        delBtn.addEventListener('click', e => { e.stopPropagation(); guardedAction(() => deleteMainSection(item.id)); });
      }
      if (type === 'subject') {
        addBtn.title = 'إضافة صف';
        addBtn.addEventListener('click', e => { e.stopPropagation(); guardedAction(() => openAddGradeModal(item.id)); });
        delBtn.addEventListener('click', e => { e.stopPropagation(); guardedAction(() => deleteSubject(item.id)); });
      }
      if (type === 'main-child') {
        addBtn.style.visibility='hidden';
        delBtn.addEventListener('click', e => { e.stopPropagation(); guardedAction(() => deleteMainChild(item.parentId,item.id)); });
      }
      if (type === 'subject-grade') {
        addBtn.style.visibility='hidden';
        delBtn.addEventListener('click', e => { e.stopPropagation(); guardedAction(() => deleteGrade(item.parentId,item.id)); });
      }
      return card;
    }

    function openMainSection(section,countVisit=true){
      if (countVisit) apiPost('/api/visit-section',{id:section.id,label:section.title});
      ui.level='sub'; ui.currentType='main'; ui.currentId=section.id; ui.currentTitle=section.title;
      subBreadcrumb.textContent=section.title; subToolbarActions.innerHTML=''; subView.classList.add('active'); filesView.classList.remove('active');
      if (!section.children || !section.children.length) subGrid.innerHTML='<div class="empty">لا توجد أقسام فرعية داخل هذا القسم. يمكنك إضافة قسم فرعي من زر الإضافة داخل البطاقة الرئيسية.</div>';
      else { subGrid.innerHTML=''; section.children.forEach(child => subGrid.appendChild(createItemCard({...child,parentId:section.id,breadcrumb:`${section.title} / ${child.title}`},'main-child'))); }
      window.scrollTo({top:subView.offsetTop-70,behavior:'smooth'}); renderStats(); renderCharts();
    }

    function openSubject(subject,countVisit=true){
      if (countVisit) apiPost('/api/visit-section',{id:subject.id,label:subject.title});
      ui.level='sub'; ui.currentType='subject'; ui.currentId=subject.id; ui.currentTitle=subject.title;
      subBreadcrumb.textContent=subject.title; subToolbarActions.innerHTML='<span class="muted">يمكن حذف الصف من داخل بطاقته، أو إضافة صف جديد للمادة.</span>';
      subView.classList.add('active'); filesView.classList.remove('active'); subGrid.innerHTML='';
      if (!subject.grades || !subject.grades.length) subGrid.innerHTML='<div class="empty">لا توجد صفوف داخل هذه المادة حاليًا.</div>';
      else subject.grades.forEach((grade,index) => subGrid.appendChild(createItemCard({id:`grade-${index}`,title:grade,icon:'📘',desc:`ملفات HTML الخاصة بـ ${grade}`,parentId:subject.id,breadcrumb:`${subject.title} / ${grade}`},'subject-grade')));
      window.scrollTo({top:subView.offsetTop-70,behavior:'smooth'}); renderStats(); renderCharts();
    }

    async function openFiles(type,parentId,itemId,title,breadcrumb){
      ui.level='files'; ui.currentType=type; ui.currentParentId=parentId; ui.currentId=itemId; ui.currentTitle=title;
      await apiPost('/api/open-path',{key:getPathKey(),label:title});
      await fetchState();
      filesBreadcrumb.textContent=breadcrumb; filesView.classList.add('active'); renderFiles();
      window.scrollTo({top:filesView.offsetTop-70,behavior:'smooth'});
    }

    function renderFiles(){
      const weekly = getWeeklyBookData();
      filesList.innerHTML='';
      if (weekly) {
        const weeklyCard = document.createElement('div');
        weeklyCard.className = 'weekly-book-card';
        weeklyCard.innerHTML = `<div class="weekly-book-cover">${weekly.image ? `<img src="${escapeHtml(weekly.image)}" alt="غلاف الكتاب">` : '📘'}</div><div class="weekly-book-meta"><div class="weekly-book-badge">📚 بين أروقة المكتبة</div><h4>${escapeHtml(weekly.title || 'كتاب الأسبوع')}</h4><p>${escapeHtml(weekly.description || '')}</p><div class="weekly-book-quote">“${escapeHtml(weekly.quote || '')}”</div><div style="margin-top:14px;"><button class="btn btn-light" id="editWeeklyBookBtn">✏ تحديث كتاب الأسبوع</button></div></div>`;
        filesList.appendChild(weeklyCard);
        setTimeout(() => {
          const btn = document.getElementById('editWeeklyBookBtn');
          if (btn) btn.addEventListener('click', () => guardedAction(openWeeklyBookModal));
        }, 0);
      }
      const files = getCurrentFiles(); filesList.innerHTML='';
      if (!files.length){ filesList.innerHTML='<div class="empty">لا توجد ملفات مضافة داخل هذا المسار حتى الآن.</div>'; renderStats(); renderCharts(); updateQuickCounters(); return; }
      files.forEach(file => {
        const liked = hasLiked(file.id);
        const card = document.createElement('div'); card.className='file-card';
        card.innerHTML = `<div><h5>📄 ${escapeHtml(file.title)}</h5><div class="date">تاريخ الرفع: ${escapeHtml(file.upload_date)}</div><div class="file-stats"><span>👁 ${file.views || 0} مشاهدة</span><span>👤 ${(file.unique_viewers || []).length} مشاهدًا</span><span>👍 ${file.likes || 0} إعجاب</span></div></div><div class="file-actions"><button class="btn btn-primary open">🔗 فتح الملف</button><button class="btn btn-light btn-like ${liked ? 'active' : ''}">👍 إعجاب</button><button class="btn btn-light rename">✏ إعادة تسمية</button><button class="btn btn-danger delete">🗑 حذف</button></div>`;
        card.querySelector('.open').addEventListener('click', () => openHtmlFile(file.id));
        card.querySelector('.btn-like').addEventListener('click', () => likeFile(file.id));
        card.querySelector('.rename').addEventListener('click', () => guardedAction(() => renameFile(file.id)));
        card.querySelector('.delete').addEventListener('click', () => guardedAction(() => deleteFile(file.id)));
        filesList.appendChild(card);
      });
      renderStats(); renderCharts(); updateQuickCounters();
    }

    function getWeeklyBookData(){
      if(ui.currentType !== 'main-child') return null;
      const parent = state.main_sections.find(s => s.id === ui.currentParentId);
      if(!parent) return null;
      const child = (parent.children || []).find(c => c.id === ui.currentId);
      if(!child || child.id !== 'library-corridors') return null;
      return child.weekly_book || null;
    }

    function openWeeklyBookModal(){
      const weekly = getWeeklyBookData();
      if(!weekly) return;
      modalBox.innerHTML = `<h3>تحديث كتاب الأسبوع</h3><p>يمكنك تحديث محتوى قسم بين أروقة المكتبة من هنا.</p><input class="input" id="weeklyTitle" value="${escapeHtml(weekly.title || '')}" placeholder="اسم الكتاب" /><input class="input" id="weeklyImage" value="${escapeHtml(weekly.image || '')}" placeholder="رابط صورة الغلاف (اختياري)" /><input class="input" id="weeklyQuote" value="${escapeHtml(weekly.quote || '')}" placeholder="الاقتباس" /><textarea class="input" id="weeklyDesc" placeholder="نبذة مختصرة عن الكتاب" style="min-height:120px; resize:vertical;">${escapeHtml(weekly.description || '')}</textarea><div class="modal-actions"><button class="btn btn-light" id="cancelWeeklyBtn">إلغاء</button><button class="btn btn-primary" id="saveWeeklyBtn">حفظ التحديث</button></div>`;
      openModal();
      document.getElementById('cancelWeeklyBtn').onclick = closeModal;
      document.getElementById('saveWeeklyBtn').onclick = async () => {
        const res = await apiPost('/api/weekly-book/update', {code: ADMIN_CODE, parent_id: ui.currentParentId, child_id: ui.currentId, title: document.getElementById('weeklyTitle').value.trim(), image: document.getElementById('weeklyImage').value.trim(), quote: document.getElementById('weeklyQuote').value.trim(), description: document.getElementById('weeklyDesc').value.trim()});
        if(!res.ok) return showToast(res.message || 'تعذر تحديث كتاب الأسبوع');
        closeModal();
        await fetchState();
        renderFiles();
        showToast('تم تحديث كتاب الأسبوع بنجاح.');
      };
    }

    function getPathKey(){ return `${ui.currentType}:${ui.currentParentId}:${ui.currentId}`; }
    function getCurrentFiles(){ return state.paths[getPathKey()]?.files || []; }
    function getAllFiles(){ return Object.values(state.paths || {}).flatMap(p => p.files || []); }
    function hasLiked(fileId){ return !!state.likes_by_visitor?.[getVisitorId()]?.[fileId]; }

    async function openHtmlFile(fileId){
      const res = await apiPost('/api/file/open',{path_key:getPathKey(),file_id:fileId,visitor_id:getVisitorId()});
      if (!res.ok) return;
      window.open(`/file/${encodeURIComponent(res.filename)}`,'_blank');
      await fetchState(); renderFiles(); showToast('تم فتح الملف وتحديث عدد المشاهدات.');
    }

    async function likeFile(fileId){
      const res = await apiPost('/api/file/like',{path_key:getPathKey(),file_id:fileId,visitor_id:getVisitorId()});
      if (!res.ok){ showToast(res.message || 'تعذر تسجيل الإعجاب'); return; }
      await fetchState(); renderFiles(); showToast('تم تسجيل الإعجاب بنجاح.');
    }

    function renameFile(fileId){
      const file = getCurrentFiles().find(f => f.id === fileId); if (!file) return;
      openPromptModal('إعادة تسمية الملف','أدخلي عنوان الملف الجديد.',file.title,'حفظ', async value => {
        if (!value.trim()) return showToast('عنوان الملف لا يمكن أن يكون فارغًا.');
        const res = await apiPost('/api/file/rename',{code:ADMIN_CODE,path_key:getPathKey(),file_id:fileId,title:value.trim()});
        if (!res.ok) return showToast(res.message || 'تعذر إعادة التسمية');
        closeModal(); await fetchState(); renderFiles(); showToast('تمت إعادة تسمية الملف بنجاح.');
      });
    }

    function deleteFile(fileId){
      openConfirmModal('حذف الملف','هل تريدين حذف هذا الملف نهائيًا؟','حذف','btn-danger', async () => {
        const res = await apiPost('/api/file/delete',{code:ADMIN_CODE,path_key:getPathKey(),file_id:fileId});
        if (!res.ok) return showToast(res.message || 'تعذر حذف الملف');
        await fetchState(); renderFiles(); showToast('تم حذف الملف بنجاح.');
      });
    }

    function openAddFileModal(){
      modalBox.innerHTML = `<h3>إضافة ملف HTML</h3><p>ارفعي ملف HTML وسيتم حفظه داخل الخادم مع تاريخ الرفع والإحصائيات.</p><input class="input" id="fileTitleInput" placeholder="عنوان الملف الظاهر داخل المنصة" /><input class="file-input" id="htmlFileInput" type="file" accept=".html,text/html" /><div class="modal-actions"><button class="btn btn-light" id="cancelBtn">إلغاء</button><button class="btn btn-primary" id="saveBtn">حفظ الملف</button></div>`;
      openModal(); document.getElementById('cancelBtn').onclick = closeModal;
      document.getElementById('saveBtn').onclick = async () => {
        const title = document.getElementById('fileTitleInput').value.trim();
        const fileInput = document.getElementById('htmlFileInput');
        if (!title) return showToast('أدخلي عنوان الملف أولًا.');
        if (!fileInput.files || !fileInput.files[0]) return showToast('اختاري ملف HTML أولًا.');
        const form = new FormData(); form.append('code', ADMIN_CODE); form.append('path_key', getPathKey()); form.append('title', title); form.append('file', fileInput.files[0]);
        const res = await fetch('/api/file/add',{method:'POST',body:form}); const data = await res.json();
        if (!data.ok) return showToast(data.message || 'تعذر إضافة الملف');
        closeModal(); await fetchState(); renderFiles(); showToast('تمت إضافة الملف بنجاح.');
      };
    }

    function openAddMainSectionModal(){
      openComplexModal({title:'إضافة قسم رئيسي',message:'أدخلي اسم القسم ووصفه والأيقونة المناسبة له.',fields:[{id:'title',placeholder:'اسم القسم'},{id:'icon',placeholder:'الأيقونة مثل 📁 أو ⚙ أو 📘'},{id:'desc',placeholder:'وصف مختصر للقسم'}], onSave: async values => {
        if (!values.title.trim()) return showToast('اسم القسم مطلوب.');
        const res = await apiPost('/api/main-section/add',{code:ADMIN_CODE,title:values.title.trim(),icon:values.icon.trim() || '📁',desc:values.desc.trim() || 'قسم مضاف حديثًا.'});
        if (!res.ok) return showToast(res.message || 'تعذر إضافة القسم');
        closeModal(); await fetchState(); renderMainSections(); renderStats(); renderCharts(); updateQuickCounters(); showToast('تمت إضافة القسم الرئيسي.');
      }});
    }

    function openAddMainChildModal(parentId){
      const parent = state.main_sections.find(s => s.id === parentId); if (!parent) return;
      openComplexModal({title:`إضافة قسم فرعي إلى ${parent.title}`,message:'أدخلي اسم القسم الفرعي ووصفه وأيقونته.',fields:[{id:'title',placeholder:'اسم القسم الفرعي'},{id:'icon',placeholder:'الأيقونة'},{id:'desc',placeholder:'وصف مختصر'}], onSave: async values => {
        if (!values.title.trim()) return showToast('اسم القسم الفرعي مطلوب.');
        const res = await apiPost('/api/main-child/add',{code:ADMIN_CODE,parent_id:parentId,title:values.title.trim(),icon:values.icon.trim() || '📚',desc:values.desc.trim() || 'قسم فرعي مضاف حديثًا.'});
        if (!res.ok) return showToast(res.message || 'تعذر إضافة القسم الفرعي');
        closeModal(); await fetchState(); renderMainSections(); const updatedParent = state.main_sections.find(s => s.id === parentId); if (ui.currentType === 'main' && updatedParent) openMainSection(updatedParent,false); showToast('تمت إضافة القسم الفرعي.');
      }});
    }

    function openAddSubjectModal(){
      openComplexModal({title:'إضافة مادة دراسية',message:'أدخلي اسم المادة ووصفها وأيقونتها.',fields:[{id:'title',placeholder:'اسم المادة'},{id:'icon',placeholder:'الأيقونة'},{id:'desc',placeholder:'وصف مختصر للمادة'}], onSave: async values => {
        if (!values.title.trim()) return showToast('اسم المادة مطلوب.');
        const res = await apiPost('/api/subject/add',{code:ADMIN_CODE,title:values.title.trim(),icon:values.icon.trim() || '📘',desc:values.desc.trim() || 'مادة دراسية مضافة حديثًا.'});
        if (!res.ok) return showToast(res.message || 'تعذر إضافة المادة');
        closeModal(); await fetchState(); renderSubjects(); renderStats(); renderCharts(); updateQuickCounters(); showToast('تمت إضافة المادة الدراسية.');
      }});
    }

    function openAddGradeModal(subjectId){
      const subject = state.subjects.find(s => s.id === subjectId); if (!subject) return;
      openPromptModal(`إضافة صف إلى ${subject.title}`,'أدخلي اسم الصف أو المسار الجديد كما سيظهر داخل المادة.','', 'إضافة', async value => {
        if (!value.trim()) return showToast('اسم الصف مطلوب.');
        const res = await apiPost('/api/grade/add',{code:ADMIN_CODE,subject_id:subjectId,title:value.trim()});
        if (!res.ok) return showToast(res.message || 'تعذر إضافة الصف');
        closeModal(); await fetchState(); const updated = state.subjects.find(s => s.id === subjectId); if (ui.currentType === 'subject' && updated) openSubject(updated,false); renderSubjects(); showToast('تمت إضافة الصف بنجاح.');
      });
    }

    function deleteMainSection(sectionId){ openConfirmModal('حذف القسم الرئيسي','سيتم حذف القسم الرئيسي وكل مساراته الفرعية وملفاته. هل تريدين المتابعة؟','حذف','btn-danger', async () => { const res = await apiPost('/api/main-section/delete',{code:ADMIN_CODE,section_id:sectionId}); if (!res.ok) return showToast(res.message || 'تعذر حذف القسم'); await fetchState(); renderMainSections(); subView.classList.remove('active'); filesView.classList.remove('active'); renderStats(); renderCharts(); updateQuickCounters(); showToast('تم حذف القسم الرئيسي.'); }); }
    function deleteMainChild(parentId,childId){ openConfirmModal('حذف القسم الفرعي','سيتم حذف القسم الفرعي وملفاته. هل تريدين المتابعة؟','حذف','btn-danger', async () => { const res = await apiPost('/api/main-child/delete',{code:ADMIN_CODE,parent_id:parentId,child_id:childId}); if (!res.ok) return showToast(res.message || 'تعذر حذف القسم الفرعي'); await fetchState(); const parent = state.main_sections.find(s => s.id === parentId); if (parent) openMainSection(parent,false); renderStats(); renderCharts(); updateQuickCounters(); showToast('تم حذف القسم الفرعي.'); }); }
    function deleteSubject(subjectId){ openConfirmModal('حذف المادة الدراسية','سيتم حذف المادة وكل الصفوف والملفات التابعة لها. هل تريدين المتابعة؟','حذف','btn-danger', async () => { const res = await apiPost('/api/subject/delete',{code:ADMIN_CODE,subject_id:subjectId}); if (!res.ok) return showToast(res.message || 'تعذر حذف المادة'); await fetchState(); renderSubjects(); subView.classList.remove('active'); filesView.classList.remove('active'); renderStats(); renderCharts(); updateQuickCounters(); showToast('تم حذف المادة الدراسية.'); }); }
    function deleteGrade(subjectId,gradeId){ openConfirmModal('حذف الصف','سيتم حذف الصف وملفاته. هل تريدين المتابعة؟','حذف','btn-danger', async () => { const res = await apiPost('/api/grade/delete',{code:ADMIN_CODE,subject_id:subjectId,grade_id:gradeId}); if (!res.ok) return showToast(res.message || 'تعذر حذف الصف'); await fetchState(); const updated = state.subjects.find(s => s.id === subjectId); if (updated) openSubject(updated,false); renderStats(); renderCharts(); updateQuickCounters(); showToast('تم حذف الصف بنجاح.'); }); }

    function guardedAction(actionFn){
      modalBox.innerHTML = `<h3>تحقق أمني</h3><p>هذه العملية محمية. أدخلي الرمز السري للمتابعة.</p><input class="input" id="adminCodeInput" type="password" placeholder="أدخلي الرمز السري" /><div class="modal-actions"><button class="btn btn-light" id="cancelCodeBtn">إلغاء</button><button class="btn btn-primary" id="confirmCodeBtn">تأكيد</button></div>`;
      openModal(); document.getElementById('cancelCodeBtn').onclick = closeModal;
      document.getElementById('confirmCodeBtn').onclick = () => { const code = document.getElementById('adminCodeInput').value; if (code !== ADMIN_CODE) return showToast('الرمز السري غير صحيح'); closeModal(); actionFn(); };
    }
    function openPromptModal(title,message,defaultValue,confirmText,onConfirm){ modalBox.innerHTML = `<h3>${escapeHtml(title)}</h3><p>${escapeHtml(message)}</p><input class="input" id="promptInput" value="${escapeHtml(defaultValue || '')}" /><div class="modal-actions"><button class="btn btn-light" id="cancelPromptBtn">إلغاء</button><button class="btn btn-primary" id="confirmPromptBtn">${escapeHtml(confirmText)}</button></div>`; openModal(); document.getElementById('cancelPromptBtn').onclick = closeModal; document.getElementById('confirmPromptBtn').onclick = () => onConfirm(document.getElementById('promptInput').value); }
    function openComplexModal({title,message,fields,onSave}){ modalBox.innerHTML = `<h3>${escapeHtml(title)}</h3><p>${escapeHtml(message)}</p>${fields.map(f => `<input class="input" data-field="${escapeHtml(f.id)}" placeholder="${escapeHtml(f.placeholder)}" />`).join('')}<div class="modal-actions"><button class="btn btn-light" id="cancelComplexBtn">إلغاء</button><button class="btn btn-primary" id="saveComplexBtn">حفظ</button></div>`; openModal(); document.getElementById('cancelComplexBtn').onclick = closeModal; document.getElementById('saveComplexBtn').onclick = () => { const values = {}; modalBox.querySelectorAll('[data-field]').forEach(el => values[el.dataset.field] = el.value || ''); onSave(values); }; }
    function openConfirmModal(title,message,confirmText,confirmClass,onConfirm){ modalBox.innerHTML = `<h3>${escapeHtml(title)}</h3><p>${escapeHtml(message)}</p><div class="modal-actions"><button class="btn btn-light" id="cancelConfirmBtn">إلغاء</button><button class="btn ${confirmClass}" id="confirmActionBtn">${escapeHtml(confirmText)}</button></div>`; openModal(); document.getElementById('cancelConfirmBtn').onclick = closeModal; document.getElementById('confirmActionBtn').onclick = () => { onConfirm(); closeModal(); }; }
    function openModal(){ modalOverlay.classList.add('active'); } function closeModal(){ modalOverlay.classList.remove('active'); modalBox.innerHTML=''; }

    function renderStats(){
      const allFiles = getAllFiles(); const totalViews = allFiles.reduce((sum,f) => sum + (f.views || 0), 0); const totalLikes = allFiles.reduce((sum,f) => sum + (f.likes || 0), 0);
      const topFile = allFiles.slice().sort((a,b) => (b.views||0) - (a.views||0))[0]; const topSection = getTopEntry(state.section_visits || {}); const topPath = getTopEntry(state.path_opens || {});
      statsGrid.innerHTML = `<div class="stat-card"><h5>عدد زوار الصفحة</h5><div class="big">${state.page_visits || 0}</div><div class="small">عدد مرات فتح الصفحة الرئيسية.</div></div><div class="stat-card"><h5>إجمالي المشاهدات</h5><div class="big">${totalViews}</div><div class="small">مجموع مرات فتح جميع ملفات HTML.</div></div><div class="stat-card"><h5>إجمالي الإعجابات</h5><div class="big">${totalLikes}</div><div class="small">مجموع الإعجابات المسجلة لكل الملفات.</div></div><div class="stat-card"><h5>أكثر الملفات مشاهدة</h5><div class="big">${topFile ? escapeHtml(topFile.title) : 'لا يوجد'}</div><div class="small">${topFile ? `عدد المشاهدات: ${topFile.views || 0}` : 'لم تتم إضافة ملفات بعد.'}</div></div><div class="stat-card"><h5>أكثر الأقسام زيارة</h5><div class="big">${topSection ? escapeHtml(topSection.label) : 'لا يوجد'}</div><div class="small">${topSection ? `عدد الزيارات: ${topSection.count}` : 'لا توجد بيانات بعد.'}</div></div><div class="stat-card"><h5>أكثر الصفوف تفاعلًا</h5><div class="big">${topPath ? escapeHtml(topPath.label) : 'لا يوجد'}</div><div class="small">${topPath ? `عدد مرات الفتح: ${topPath.count}` : 'لا توجد بيانات بعد.'}</div></div>`;
    }

    function renderCharts(){
      const allFiles = getAllFiles();

      const fileNames = allFiles.map(f=>f.title);
      const fileViews = allFiles.map(f=>f.views||0);

      const ctx1 = document.getElementById('viewsChart');
      if(ctx1){
        new Chart(ctx1,{type:'bar',data:{labels:fileNames,datasets:[{label:'عدد المشاهدات',data:fileViews}]}});
      }

      const sections = Object.values(state.section_visits||{});
      const sectionNames = sections.map(s=>s.label);
      const sectionCounts = sections.map(s=>s.count);

      const ctx2 = document.getElementById('sectionsChart');
      if(ctx2){
        new Chart(ctx2,{type:'pie',data:{labels:sectionNames,datasets:[{data:sectionCounts}]}});
      }
    }

    function updateQuickCounters(){ const allFiles = getAllFiles(); const totalViews = allFiles.reduce((sum,f) => sum + (f.views || 0), 0); const totalLikes = allFiles.reduce((sum,f) => sum + (f.likes || 0), 0); document.getElementById('visitsCount').textContent = state.page_visits || 0; document.getElementById('viewsCount').textContent = totalViews; document.getElementById('likesCount').textContent = totalLikes; document.getElementById('filesCount').textContent = allFiles.length; }
    function getTopEntry(obj){ const arr = Object.values(obj || {}); if (!arr.length) return null; return arr.sort((a,b) => b.count - a.count)[0]; }
    function getVisitorId(){ let id = localStorage.getItem('flask_library_visitor_id'); if (!id){ id = `visitor_${Math.random().toString(36).slice(2,9)}_${Date.now()}`; localStorage.setItem('flask_library_visitor_id', id); } return id; }
    async function apiPost(url,payload){ const res = await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)}); return await res.json(); }
    function showToast(message){ toast.textContent = message; toast.classList.add('show'); clearTimeout(showToast.timer); showToast.timer = setTimeout(() => toast.classList.remove('show'), 2400); }
    function attachSearch() {
      const input = document.getElementById('searchInput');
      if (!input) return;
      input.addEventListener('input', () => {
        const q = input.value.toLowerCase();
        document.querySelectorAll('#mainSectionsGrid .card').forEach(card => {
          card.style.display = card.innerText.toLowerCase().includes(q) ? '' : 'none';
        });
        document.querySelectorAll('#subjectsGrid .card').forEach(card => {
          card.style.display = card.innerText.toLowerCase().includes(q) ? '' : 'none';
        });
        document.querySelectorAll('#filesList .file-card').forEach(card => {
          card.style.display = card.innerText.toLowerCase().includes(q) ? '' : 'none';
        });
      });
    }

    function escapeHtml(text=''){ return String(text).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#039;'); }
  </script>
</body>
</html>
'''


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def today_ar() -> str:
    days = ["الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]
    months = ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو", "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"]
    now = datetime.now()
    return f"{days[now.weekday()]} {now.day} {months[now.month - 1]} {now.year}"


def load_state() -> dict[str, Any]:
    if not DATA_FILE.exists():
        save_state(DEFAULT_STATE)
        return json.loads(json.dumps(DEFAULT_STATE))
    with DATA_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state: dict[str, Any]) -> None:
    with DATA_FILE.open("w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def ok(**kwargs):
    return jsonify({"ok": True, **kwargs})


def fail(message: str, status: int = 400):
    return jsonify({"ok": False, "message": message}), status


def require_code(payload: dict[str, Any]) -> bool:
    return payload.get("code") == ADMIN_CODE


def get_path(state: dict[str, Any], path_key: str) -> dict[str, Any]:
    state.setdefault("paths", {})
    state["paths"].setdefault(path_key, {"files": []})
    return state["paths"][path_key]


def delete_file_disk(filename: str | None) -> None:
    if not filename:
        return
    path = UPLOADS_DIR / filename
    if path.exists():
        path.unlink()


@app.route("/")
def index():
    state = load_state()
    state["page_visits"] = state.get("page_visits", 0) + 1
    save_state(state)
    return render_template_string(INDEX_HTML)


@app.route("/file/<path:filename>")
def serve_uploaded_file(filename: str):
    return send_from_directory(UPLOADS_DIR, filename)


@app.route("/api/state")
def api_state():
    return jsonify(load_state())


@app.post("/api/visit-section")
def api_visit_section():
    payload = request.get_json(force=True)
    state = load_state()
    state.setdefault("section_visits", {})
    entry = state["section_visits"].setdefault(payload["id"], {"label": payload["label"], "count": 0})
    entry["label"] = payload["label"]
    entry["count"] += 1
    save_state(state)
    return ok()


@app.post("/api/open-path")
def api_open_path():
    payload = request.get_json(force=True)
    state = load_state()
    get_path(state, payload["key"])
    state.setdefault("path_opens", {})
    entry = state["path_opens"].setdefault(payload["key"], {"label": payload["label"], "count": 0})
    entry["label"] = payload["label"]
    entry["count"] += 1
    save_state(state)
    return ok()


@app.post("/api/file/add")
def api_file_add():
    code = request.form.get("code", "")
    if code != ADMIN_CODE:
        return fail("الرمز السري غير صحيح", 403)
    uploaded = request.files.get("file")
    title = request.form.get("title", "").strip()
    path_key = request.form.get("path_key", "").strip()
    if not uploaded or not title or not path_key:
        return fail("البيانات غير مكتملة")
    ext = Path(uploaded.filename or "").suffix.lower()
    if ext != ".html":
        return fail("يسمح فقط برفع ملفات HTML")

    state = load_state()
    path = get_path(state, path_key)
    safe_name = secure_filename(uploaded.filename or f"{new_id('file')}.html")
    final_name = f"{uuid.uuid4().hex[:10]}_{safe_name}"
    uploaded.save(UPLOADS_DIR / final_name)
    path["files"].insert(0, {
        "id": new_id("file"),
        "title": title,
        "filename": final_name,
        "upload_date": today_ar(),
        "views": 0,
        "unique_viewers": [],
        "likes": 0,
    })
    save_state(state)
    return ok()


@app.post("/api/file/open")
def api_file_open():
    payload = request.get_json(force=True)
    state = load_state()
    files = get_path(state, payload["path_key"])["files"]
    file = next((f for f in files if f["id"] == payload["file_id"]), None)
    if not file:
        return fail("الملف غير موجود", 404)
    file["views"] = file.get("views", 0) + 1
    file.setdefault("unique_viewers", [])
    visitor_id = payload.get("visitor_id", "")
    if visitor_id and visitor_id not in file["unique_viewers"]:
        file["unique_viewers"].append(visitor_id)
    save_state(state)
    return ok(filename=file["filename"])


@app.post("/api/file/like")
def api_file_like():
    payload = request.get_json(force=True)
    state = load_state()
    visitor_id = payload.get("visitor_id", "")
    if not visitor_id:
        return fail("معرّف الزائر مفقود")
    state.setdefault("likes_by_visitor", {})
    state["likes_by_visitor"].setdefault(visitor_id, {})
    if state["likes_by_visitor"][visitor_id].get(payload["file_id"]):
        return fail("تم تسجيل إعجابك مسبقًا لهذا الملف")
    files = get_path(state, payload["path_key"])["files"]
    file = next((f for f in files if f["id"] == payload["file_id"]), None)
    if not file:
        return fail("الملف غير موجود", 404)
    state["likes_by_visitor"][visitor_id][payload["file_id"]] = True
    file["likes"] = file.get("likes", 0) + 1
    save_state(state)
    return ok()


@app.post("/api/file/rename")
def api_file_rename():
    payload = request.get_json(force=True)
    if not require_code(payload):
        return fail("الرمز السري غير صحيح", 403)
    title = payload.get("title", "").strip()
    if not title:
        return fail("عنوان الملف مطلوب")
    state = load_state()
    files = get_path(state, payload["path_key"])["files"]
    file = next((f for f in files if f["id"] == payload["file_id"]), None)
    if not file:
        return fail("الملف غير موجود", 404)
    file["title"] = title
    save_state(state)
    return ok()


@app.post("/api/file/delete")
def api_file_delete():
    payload = request.get_json(force=True)
    if not require_code(payload):
        return fail("الرمز السري غير صحيح", 403)
    state = load_state()
    files = get_path(state, payload["path_key"])["files"]
    index = next((i for i, f in enumerate(files) if f["id"] == payload["file_id"]), -1)
    if index == -1:
        return fail("الملف غير موجود", 404)
    deleted = files.pop(index)
    delete_file_disk(deleted.get("filename"))
    save_state(state)
    return ok()


@app.post("/api/main-section/add")
def api_main_section_add():
    payload = request.get_json(force=True)
    if not require_code(payload):
        return fail("الرمز السري غير صحيح", 403)
    state = load_state()
    state["main_sections"].append({
        "id": new_id("main"),
        "title": payload["title"],
        "icon": payload.get("icon", "📁"),
        "desc": payload.get("desc", "قسم مضاف حديثًا."),
        "children": [],
    })
    save_state(state)
    return ok()


@app.post("/api/main-section/delete")
def api_main_section_delete():
    payload = request.get_json(force=True)
    if not require_code(payload):
        return fail("الرمز السري غير صحيح", 403)
    state = load_state()
    section = next((s for s in state["main_sections"] if s["id"] == payload["section_id"]), None)
    if not section:
        return fail("القسم غير موجود", 404)
    for child in section.get("children", []):
        path_key = f"main-child:{section['id']}:{child['id']}"
        for file in state.get("paths", {}).get(path_key, {}).get("files", []):
            delete_file_disk(file.get("filename"))
        state.get("paths", {}).pop(path_key, None)
    state["main_sections"] = [s for s in state["main_sections"] if s["id"] != payload["section_id"]]
    save_state(state)
    return ok()


@app.post("/api/main-child/add")
def api_main_child_add():
    payload = request.get_json(force=True)
    if not require_code(payload):
        return fail("الرمز السري غير صحيح", 403)
    state = load_state()
    parent = next((s for s in state["main_sections"] if s["id"] == payload["parent_id"]), None)
    if not parent:
        return fail("القسم الرئيسي غير موجود", 404)
    parent.setdefault("children", []).append({
        "id": new_id("child"),
        "title": payload["title"],
        "icon": payload.get("icon", "📚"),
        "desc": payload.get("desc", "قسم فرعي مضاف حديثًا."),
    })
    save_state(state)
    return ok()


@app.post("/api/main-child/delete")
def api_main_child_delete():
    payload = request.get_json(force=True)
    if not require_code(payload):
        return fail("الرمز السري غير صحيح", 403)
    state = load_state()
    parent = next((s for s in state["main_sections"] if s["id"] == payload["parent_id"]), None)
    if not parent:
        return fail("القسم الرئيسي غير موجود", 404)
    path_key = f"main-child:{payload['parent_id']}:{payload['child_id']}"
    for file in state.get("paths", {}).get(path_key, {}).get("files", []):
        delete_file_disk(file.get("filename"))
    state.get("paths", {}).pop(path_key, None)
    parent["children"] = [c for c in parent.get("children", []) if c["id"] != payload["child_id"]]
    save_state(state)
    return ok()


@app.post("/api/weekly-book/update")
def api_weekly_book_update():
    payload = request.get_json(force=True)
    if not require_code(payload):
        return fail("الرمز السري غير صحيح", 403)
    state = load_state()
    parent = next((s for s in state["main_sections"] if s["id"] == payload["parent_id"]), None)
    if not parent:
        return fail("القسم الرئيسي غير موجود", 404)
    child = next((c for c in parent.get("children", []) if c["id"] == payload["child_id"]), None)
    if not child:
        return fail("القسم الفرعي غير موجود", 404)
    child["weekly_book"] = {
        "title": payload.get("title", "كتاب الأسبوع"),
        "description": payload.get("description", ""),
        "quote": payload.get("quote", ""),
        "image": payload.get("image", "")
    }
    save_state(state)
    return ok()


@app.post("/api/subject/add")
def api_subject_add():
    payload = request.get_json(force=True)
    if not require_code(payload):
        return fail("الرمز السري غير صحيح", 403)
    state = load_state()
    state["subjects"].append({
        "id": new_id("subject"),
        "title": payload["title"],
        "icon": payload.get("icon", "📘"),
        "desc": payload.get("desc", "مادة دراسية مضافة حديثًا."),
        "grades": [],
    })
    save_state(state)
    return ok()


@app.post("/api/subject/delete")
def api_subject_delete():
    payload = request.get_json(force=True)
    if not require_code(payload):
        return fail("الرمز السري غير صحيح", 403)
    state = load_state()
    subject = next((s for s in state["subjects"] if s["id"] == payload["subject_id"]), None)
    if not subject:
        return fail("المادة غير موجودة", 404)
    for index, _grade in enumerate(subject.get("grades", [])):
        path_key = f"subject-grade:{subject['id']}:grade-{index}"
        for file in state.get("paths", {}).get(path_key, {}).get("files", []):
            delete_file_disk(file.get("filename"))
        state.get("paths", {}).pop(path_key, None)
    state["subjects"] = [s for s in state["subjects"] if s["id"] != payload["subject_id"]]
    save_state(state)
    return ok()


@app.post("/api/grade/add")
def api_grade_add():
    payload = request.get_json(force=True)
    if not require_code(payload):
        return fail("الرمز السري غير صحيح", 403)
    state = load_state()
    subject = next((s for s in state["subjects"] if s["id"] == payload["subject_id"]), None)
    if not subject:
        return fail("المادة غير موجودة", 404)
    subject.setdefault("grades", []).append(payload["title"])
    save_state(state)
    return ok()


@app.post("/api/grade/delete")
def api_grade_delete():
    payload = request.get_json(force=True)
    if not require_code(payload):
        return fail("الرمز السري غير صحيح", 403)
    state = load_state()
    subject = next((s for s in state["subjects"] if s["id"] == payload["subject_id"]), None)
    if not subject:
        return fail("المادة غير موجودة", 404)
    grade_id = payload["grade_id"]
    if not grade_id.startswith("grade-"):
        return fail("معرّف الصف غير صحيح")
    index = int(grade_id.split("-")[1])
    if index < 0 or index >= len(subject.get("grades", [])):
        return fail("الصف غير موجود", 404)
    path_key = f"subject-grade:{subject['id']}:{grade_id}"
    for file in state.get("paths", {}).get(path_key, {}).get("files", []):
        delete_file_disk(file.get("filename"))
    state.get("paths", {}).pop(path_key, None)
    subject["grades"].pop(index)
    save_state(state)
    return ok()


if __name__ == "__main__":
    app.run(debug=True)



