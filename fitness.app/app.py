from datetime import date, datetime, timedelta

import pandas as pd
import streamlit as st

from data import EXERCISES
from recommender import recommend_workout
from storage import (
    delete_profile,
    load_profile,
    load_profiles,
    load_records,
    load_workout_list,
    save_profile,
    save_record,
    save_records,
    save_workout_list,
)

st.set_page_config(page_title="운동 프로그램", layout="wide")

WEEKDAYS = ["월", "화", "수", "목", "금", "토", "일"]

EMPTY_PROFILE = {
    "username": "",
    "level": "초보자",
    "height": 175,
    "weight": 70,
    "goal": "근비대",
    "workout_days": [],
}

st.markdown(
    """
    <style>
    .weekday-row {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        margin: 8px 0 16px 0;
    }
    .weekday-chip-on {
        padding: 6px 12px;
        border-radius: 999px;
        background: #16a34a;
        color: white;
        font-weight: 700;
        font-size: 14px;
    }
    .weekday-chip-off {
        padding: 6px 12px;
        border-radius: 999px;
        background: #e5e7eb;
        color: #4b5563;
        font-weight: 700;
        font-size: 14px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if "profile_loaded" not in st.session_state:
    st.session_state.profile_loaded = False

if "profile" not in st.session_state:
    st.session_state.profile = EMPTY_PROFILE.copy()

if "selected_by_day" not in st.session_state:
    st.session_state.selected_by_day = {day: [] for day in WEEKDAYS}

if "weekday_selection" not in st.session_state:
    st.session_state.weekday_selection = {day: False for day in WEEKDAYS}

if "step2_day" not in st.session_state:
    st.session_state.step2_day = "월"

if "step3_day" not in st.session_state:
    st.session_state.step3_day = "월"


def reset_current_profile():
    st.session_state.profile_loaded = False
    st.session_state.profile = EMPTY_PROFILE.copy()
    st.session_state.selected_by_day = {day: [] for day in WEEKDAYS}
    st.session_state.weekday_selection = {day: False for day in WEEKDAYS}
    st.session_state.step2_day = "월"
    st.session_state.step3_day = "월"


def is_this_week(date_text):
    try:
        record_date = datetime.strptime(date_text, "%Y-%m-%d").date()
    except ValueError:
        return False

    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    return week_start <= record_date <= week_end


def get_today_weekday():
    return WEEKDAYS[date.today().weekday()]


def get_week_records(records, username):
    return [
        record
        for record in records
        if record.get("username") == username and is_this_week(record.get("date", ""))
    ]


def recalculate_record_totals(record):
    total_calories = 0
    total_minutes = 0

    for workout in record.get("workouts", []):
        total_calories += int(workout.get("calories", 0))
        total_minutes += int(workout.get("minutes", 0))

    record["total_calories"] = total_calories
    record["total_minutes"] = total_minutes

    return record


def delete_workout_and_save(records, record_index, workout_index):
    workouts = records[record_index].get("workouts", [])

    if 0 <= workout_index < len(workouts):
        workouts.pop(workout_index)

    if workouts:
        records[record_index]["workouts"] = workouts
        records[record_index] = recalculate_record_totals(records[record_index])
    else:
        records.pop(record_index)

    save_records(records)


def load_day_list(username, day):
    st.session_state.selected_by_day[day] = load_workout_list(username, day)


def load_saved_lists_into_session(username, workout_days):
    for day in workout_days:
        st.session_state.selected_by_day[day] = load_workout_list(username, day)


def get_selected_weekdays():
    return [
        day
        for day in WEEKDAYS
        if st.session_state.weekday_selection.get(day, False)
    ]


def render_weekday_badges(selected_days):
    html = '<div class="weekday-row">'

    for day in WEEKDAYS:
        class_name = "weekday-chip-on" if day in selected_days else "weekday-chip-off"
        html += f'<span class="{class_name}">{day}</span>'

    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def sync_weekday_selection_from_profile(profile):
    saved_days = profile.get("workout_days", [])
    st.session_state.weekday_selection = {
        day: day in saved_days
        for day in WEEKDAYS
    }


def set_active_profile(profile):
    if "workout_days" not in profile:
        profile["workout_days"] = WEEKDAYS[: int(profile.get("weekly_days", 3))]

    st.session_state.profile = profile
    st.session_state.profile_loaded = True
    sync_weekday_selection_from_profile(profile)
    load_saved_lists_into_session(profile["username"], profile["workout_days"])

    if profile["workout_days"]:
        st.session_state.step2_day = profile["workout_days"][0]
        st.session_state.step3_day = profile["workout_days"][0]


def render_compact_selected_workouts(username, selected_day):
    workouts = st.session_state.selected_by_day.get(selected_day, [])

    st.subheader(f"{selected_day}요일 선택된 운동")

    if not workouts:
        st.info("아직 선택된 운동이 없습니다.")
        return

    for index, item in enumerate(workouts):
        with st.container(border=True):
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])

            with col1:
                st.write(f"**{item.get('name', '')}**")
                st.caption(
                    f"{item.get('category', '')} / "
                    f"{item.get('group', '')} / "
                    f"{item.get('part', '')}"
                )

            with col2:
                st.write(f"{item.get('weight', 0):g}kg")
                st.caption(f"{item.get('reps', 0)}회 x {item.get('sets', 0)}세트")

            with col3:
                st.write(f"{item.get('calories', 0)} kcal")
                st.caption(f"휴식 {item.get('rest', 0)}초")

            with col4:
                if st.button("삭제", key=f"step2_delete_{selected_day}_{index}"):
                    workouts.pop(index)
                    st.session_state.selected_by_day[selected_day] = workouts
                    save_workout_list(username, selected_day, workouts)
                    st.success("선택된 운동을 삭제했습니다.")
                    st.rerun()


st.title("운동 프로그램 웹앱")

menu = st.sidebar.radio(
    "메뉴",
    ["사용자 정보", "운동 선택", "요일별 운동 리스트", "주간 통계"],
)

profile = st.session_state.profile
profile_loaded = st.session_state.profile_loaded
current_username = profile.get("username", "")
workout_days = profile.get("workout_days", [])

st.sidebar.write("---")
st.sidebar.write("현재 사용자 정보")

if profile_loaded:
    st.sidebar.write(f"이름: {current_username}")
    st.sidebar.write(f"수준: {profile['level']}")
    st.sidebar.write(f"키: {profile['height']}cm")
    st.sidebar.write(f"몸무게: {profile['weight']}kg")
    st.sidebar.write(f"목표: {profile['goal']}")
    st.sidebar.write(f"운동 요일: {', '.join(workout_days) if workout_days else '미설정'}")
else:
    st.sidebar.info("사용자 정보를 입력하거나 저장된 정보를 불러오세요.")

if menu == "사용자 정보":
    st.header("Step 1. 사용자 정보 입력 / 불러오기 / 삭제")

    if not profile_loaded:
        st.info("처음 실행 화면입니다. 새 사용자 정보를 입력하거나 저장된 사용자 정보를 불러오세요.")

    profiles = load_profiles()
    profile_names = list(profiles.keys())

    if profile_names:
        selected_username = st.selectbox("저장된 사용자 선택", profile_names)

        col_load, col_delete = st.columns(2)

        with col_load:
            if st.button("선택한 사용자 정보 불러오기"):
                selected_profile = load_profile(selected_username)

                if selected_profile:
                    set_active_profile(selected_profile)
                    st.success(f"{selected_username}님의 정보를 불러왔습니다.")
                    st.rerun()

        with col_delete:
            if st.button("선택한 사용자 정보 삭제"):
                delete_profile(selected_username)

                if selected_username == current_username:
                    reset_current_profile()

                st.success(f"{selected_username}님의 사용자 정보가 삭제되었습니다.")
                st.rerun()

    else:
        st.info("저장된 사용자 정보가 없습니다.")

    st.divider()

    level_options = ["입문자", "초보자", "중급자", "상급자"]
    goal_options = ["근력 증가", "근비대", "체지방 감량", "건강 관리"]

    username = st.text_input(
        "사용자 이름",
        value=profile.get("username", ""),
        placeholder="예: 홍길동",
    )

    level = st.selectbox(
        "운동 수준",
        level_options,
        index=level_options.index(profile["level"]),
    )

    height = st.number_input(
        "키(cm)",
        min_value=120,
        max_value=230,
        value=int(profile["height"]),
    )

    weight = st.number_input(
        "몸무게(kg)",
        min_value=30,
        max_value=200,
        value=int(profile["weight"]),
    )

    goal = st.selectbox(
        "운동 목표",
        goal_options,
        index=goal_options.index(profile["goal"]),
    )

    st.write("주 운동 요일 선택")
    st.caption("ON이면 초록색, OFF이면 회색으로 표시됩니다.")

    cols = st.columns(7)

    for index, day in enumerate(WEEKDAYS):
        with cols[index]:
            st.toggle(
                day,
                key=f"weekday_toggle_{day}",
                value=st.session_state.weekday_selection.get(day, False),
                on_change=lambda d=day: st.session_state.weekday_selection.update(
                    {d: st.session_state[f"weekday_toggle_{d}"]}
                ),
            )

    selected_days = get_selected_weekdays()
    render_weekday_badges(selected_days)

    if st.button("사용자 정보 저장"):
        if not username.strip():
            st.error("사용자 이름을 입력해주세요.")
        elif not selected_days:
            st.error("운동할 요일을 1개 이상 선택해주세요.")
        else:
            new_profile = {
                "username": username.strip(),
                "level": level,
                "height": int(height),
                "weight": int(weight),
                "goal": goal,
                "workout_days": selected_days,
            }

            save_profile(new_profile)
            set_active_profile(new_profile)

            st.success(f"{username}님의 사용자 정보가 저장되었습니다.")
            st.rerun()

elif not profile_loaded:
    st.header("사용자 정보가 필요합니다")
    st.info("먼저 사용자 정보 화면에서 새 정보를 입력하거나 저장된 사용자 정보를 불러오세요.")

elif menu == "운동 선택":
    st.header("Step 2. 운동 선택")

    if not workout_days:
        st.warning("사용자 정보에서 운동 요일을 먼저 선택해주세요.")
        st.stop()

    selected_day = st.selectbox(
        "운동을 추가할 요일",
        workout_days,
        key="step2_day",
    )

    if selected_day not in st.session_state.selected_by_day:
        load_day_list(current_username, selected_day)

    if not st.session_state.selected_by_day[selected_day]:
        load_day_list(current_username, selected_day)

    render_compact_selected_workouts(current_username, selected_day)

    st.divider()
    st.subheader("추가 가능한 운동")

    selected_names = {
        item["name"] for item in st.session_state.selected_by_day[selected_day]
    }

    category = st.selectbox("큰 분류", ["전체", "상체", "하체", "코어"])
    filtered = EXERCISES

    if category != "전체":
        filtered = [item for item in filtered if item["category"] == category]

    if category == "상체":
        upper_group = st.selectbox("상체 세부 분류", ["전체", "가슴", "등", "어깨", "팔"])

        if upper_group != "전체":
            filtered = [item for item in filtered if item["group"] == upper_group]

        if upper_group == "팔":
            arm_part = st.selectbox("팔 세부 분류", ["전체", "이두", "삼두"])

            if arm_part != "전체":
                filtered = [item for item in filtered if item["part"] == arm_part]

    elif category == "하체":
        lower_part = st.selectbox(
            "하체 세부 분류",
            ["전체", "대퇴사두", "햄스트링", "둔근", "종아리"],
        )

        if lower_part != "전체":
            filtered = [item for item in filtered if item["part"] == lower_part]

    available = [item for item in filtered if item["name"] not in selected_names]

    st.caption("이미 선택된 운동은 위쪽 선택된 운동 리스트에 표시되고, 아래 추가 목록에서는 제외됩니다.")

    if not available:
        st.info("현재 조건에서 추가할 수 있는 운동이 없습니다.")

    for exercise in available:
        with st.container(border=True):
            col1, col2, col3 = st.columns([3, 3, 1])

            with col1:
                st.write(f"**{exercise['name']}**")
                st.caption(
                    f"{exercise['category']} / "
                    f"{exercise['group']} / "
                    f"{exercise['part']}"
                )

            with col2:
                st.caption(f"추천 수준: {', '.join(exercise['levels'])}")
                st.link_button("자세 보기", exercise["youtube"])

            with col3:
                if profile["level"] not in exercise["levels"]:
                    st.warning("비추천")
                else:
                    if st.button("추가", key=f"add_{selected_day}_{exercise['name']}"):
                        item = recommend_workout(
                            exercise,
                            profile["level"],
                            profile["weight"],
                            profile["goal"],
                        )

                        st.session_state.selected_by_day[selected_day].append(item)

                        save_workout_list(
                            current_username,
                            selected_day,
                            st.session_state.selected_by_day[selected_day],
                        )

                        st.success(f"{selected_day}요일에 {exercise['name']} 추가 완료")
                        st.rerun()

elif menu == "요일별 운동 리스트":
    st.header("Step 3. 요일별 운동 리스트 수정 / 저장 / 완료")

    if not workout_days:
        st.warning("사용자 정보에서 운동 요일을 먼저 선택해주세요.")
        st.stop()

    selected_day = st.selectbox(
        "운동 리스트 요일",
        workout_days,
        key="step3_day",
    )

    load_day_list(current_username, selected_day)

    col_load, col_clear = st.columns(2)

    with col_load:
        st.info(f"{selected_day}요일 운동 리스트를 자동으로 불러왔습니다.")

    with col_clear:
        if st.button("이 요일 운동 리스트 전체 삭제"):
            st.session_state.selected_by_day[selected_day] = []
            save_workout_list(current_username, selected_day, [])
            st.success(f"{selected_day}요일 운동 리스트를 비웠습니다.")
            st.rerun()

    workouts = st.session_state.selected_by_day[selected_day]

    if not workouts:
        st.info("운동 선택 메뉴에서 이 요일에 운동을 추가하세요.")

    else:
        final_items = []
        total_calories = 0
        total_minutes = 0

        for index, item in enumerate(workouts):
            with st.container(border=True):
                col_title, col_delete = st.columns([4, 1])

                with col_title:
                    st.subheader(item["name"])
                    st.caption(
                        f"{item.get('category', '')} / "
                        f"{item.get('group', '')} / "
                        f"{item.get('part', '')}"
                    )

                with col_delete:
                    if st.button("삭제", key=f"delete_plan_{selected_day}_{index}"):
                        workouts.pop(index)
                        save_workout_list(current_username, selected_day, workouts)
                        st.success("운동이 삭제되었습니다.")
                        st.rerun()

                col1, col2, col3, col4 = st.columns(4)

                item["weight"] = col1.number_input(
                    "무게(kg)",
                    min_value=0.0,
                    value=float(item.get("weight", 0)),
                    step=2.5,
                    key=f"weight_{selected_day}_{index}",
                )

                item["reps"] = col2.number_input(
                    "횟수",
                    min_value=1,
                    value=int(item.get("reps", 1)),
                    key=f"reps_{selected_day}_{index}",
                )

                item["sets"] = col3.number_input(
                    "세트",
                    min_value=1,
                    value=int(item.get("sets", 1)),
                    key=f"sets_{selected_day}_{index}",
                )

                item["minutes"] = col4.number_input(
                    "운동 시간(분)",
                    min_value=1,
                    value=int(item.get("minutes", 1)),
                    key=f"minutes_{selected_day}_{index}",
                )

                item["rest"] = st.slider(
                    "세트 사이 휴식 시간(초)",
                    min_value=30,
                    max_value=240,
                    value=int(item.get("rest", 60)),
                    step=15,
                    key=f"rest_{selected_day}_{index}",
                )

                item["calories"] = st.number_input(
                    "예상 소모 칼로리",
                    min_value=0,
                    value=int(item.get("calories", 0)),
                    key=f"calories_{selected_day}_{index}",
                )

                final_items.append(item)
                total_calories += int(item["calories"])
                total_minutes += int(item["minutes"])

        st.session_state.selected_by_day[selected_day] = final_items

        st.metric("총 예상 소모 칼로리", f"{total_calories} kcal")
        st.metric("총 예상 운동 시간", f"{total_minutes}분")

        col_save, col_done = st.columns(2)

        with col_save:
            if st.button("이 요일 운동 리스트 저장"):
                save_workout_list(current_username, selected_day, final_items)
                st.success(f"{selected_day}요일 운동 리스트가 저장되었습니다.")

        with col_done:
            if st.button("오늘 운동 완료"):
                today_weekday = get_today_weekday()

                record = {
                    "date": date.today().isoformat(),
                    "weekday": today_weekday,
                    "planned_weekday": selected_day,
                    "username": current_username,
                    "profile": profile,
                    "workouts": final_items,
                    "total_calories": total_calories,
                    "total_minutes": total_minutes,
                }

                save_record(record)
                st.success("오늘 운동 기록이 저장되었습니다.")

elif menu == "주간 통계":
    st.header("Step 4. 주간 통계")
    st.caption(f"현재 선택된 사용자: {current_username}")

    records = load_records()
    week_records = get_week_records(records, current_username)

    if not week_records:
        st.info(f"{current_username}님의 이번 주 운동 기록이 없습니다.")

    else:
        total_calories = sum(record.get("total_calories", 0) for record in week_records)

        st.metric("이번 주 운동 횟수", f"{len(week_records)}회")
        st.metric("이번 주 총 소모 칼로리", f"{total_calories} kcal")

        today = date.today()
        week_start = today - timedelta(days=today.weekday())

        daily_data = {
            (week_start + timedelta(days=i)).isoformat(): 0
            for i in range(7)
        }

        for record in week_records:
            daily_data[record["date"]] += record.get("total_calories", 0)

        chart_data = pd.DataFrame(
            {
                "날짜": list(daily_data.keys()),
                "소모 칼로리": list(daily_data.values()),
            }
        )

        st.bar_chart(chart_data, x="날짜", y="소모 칼로리")

        st.subheader("이번 주 운동 기록 수정 / 삭제")

        for record_index, record in enumerate(records):
            if record.get("username") != current_username:
                continue

            if not is_this_week(record.get("date", "")):
                continue

            label_weekday = record.get("planned_weekday") or record.get("weekday", "")

            with st.expander(
                f"{record.get('date', '-')} {label_weekday} - "
                f"{record.get('total_calories', 0)} kcal"
            ):
                new_date = st.date_input(
                    "운동 날짜",
                    value=datetime.strptime(record["date"], "%Y-%m-%d").date(),
                    key=f"record_date_{record_index}",
                )

                new_weekday = st.selectbox(
                    "운동 요일",
                    WEEKDAYS,
                    index=WEEKDAYS.index(label_weekday)
                    if label_weekday in WEEKDAYS
                    else 0,
                    key=f"record_weekday_{record_index}",
                )

                updated_workouts = []
                total_record_calories = 0
                total_record_minutes = 0

                for workout_index, workout in enumerate(record.get("workouts", [])):
                    st.write("---")

                    col_title, col_delete = st.columns([4, 1])

                    with col_title:
                        st.write(f"운동 {workout_index + 1}: {workout.get('name', '')}")

                    with col_delete:
                        if st.button(
                            "삭제",
                            key=f"delete_workout_now_{record_index}_{workout_index}",
                        ):
                            delete_workout_and_save(records, record_index, workout_index)
                            st.success("운동이 삭제되었습니다.")
                            st.rerun()

                    col1, col2 = st.columns(2)

                    workout["name"] = col1.text_input(
                        "운동 이름",
                        value=workout.get("name", ""),
                        key=f"name_{record_index}_{workout_index}",
                    )

                    workout["part"] = col2.text_input(
                        "운동 부위",
                        value=workout.get("part", ""),
                        key=f"part_{record_index}_{workout_index}",
                    )

                    col3, col4, col5 = st.columns(3)

                    workout["weight"] = col3.number_input(
                        "무게(kg)",
                        min_value=0.0,
                        value=float(workout.get("weight", 0)),
                        step=2.5,
                        key=f"w_{record_index}_{workout_index}",
                    )

                    workout["reps"] = col4.number_input(
                        "횟수",
                        min_value=1,
                        value=int(workout.get("reps", 1)),
                        key=f"r_{record_index}_{workout_index}",
                    )

                    workout["sets"] = col5.number_input(
                        "세트",
                        min_value=1,
                        value=int(workout.get("sets", 1)),
                        key=f"s_{record_index}_{workout_index}",
                    )

                    col6, col7, col8 = st.columns(3)

                    workout["minutes"] = col6.number_input(
                        "운동 시간(분)",
                        min_value=1,
                        value=int(workout.get("minutes", 1)),
                        key=f"m_{record_index}_{workout_index}",
                    )

                    workout["rest"] = col7.number_input(
                        "휴식 시간(초)",
                        min_value=0,
                        value=int(workout.get("rest", 60)),
                        key=f"rest_{record_index}_{workout_index}",
                    )

                    workout["calories"] = col8.number_input(
                        "소모 칼로리",
                        min_value=0,
                        value=int(workout.get("calories", 0)),
                        key=f"cal_{record_index}_{workout_index}",
                    )

                    updated_workouts.append(workout)
                    total_record_calories += int(workout["calories"])
                    total_record_minutes += int(workout["minutes"])

                col_save, col_delete_record = st.columns(2)

                with col_save:
                    if st.button("이 기록 수정 저장", key=f"save_record_{record_index}"):
                        records[record_index]["date"] = new_date.isoformat()
                        records[record_index]["weekday"] = new_weekday
                        records[record_index]["planned_weekday"] = new_weekday
                        records[record_index]["username"] = current_username
                        records[record_index]["profile"] = profile
                        records[record_index]["workouts"] = updated_workouts
                        records[record_index]["total_calories"] = total_record_calories
                        records[record_index]["total_minutes"] = total_record_minutes

                        save_records(records)
                        st.success("운동 기록이 수정되었습니다.")
                        st.rerun()

                with col_delete_record:
                    if st.button("이 날짜 기록 전체 삭제", key=f"delete_record_{record_index}"):
                        records.pop(record_index)
                        save_records(records)

                        st.success("운동 기록이 삭제되었습니다.")
                        st.rerun()