"""
Unit tests for itinerary-related models.

移動スケジュール連携機能に関するモデルのテストを実施します。
"""

from datetime import datetime, timedelta

import pytest

from src.models import (
    AccommodationInfo,
    FlightInfo,
    Meeting,
    TransportSegment,
    TripItinerary,
)


# FlightInfo Tests
class TestFlightInfo:
    """FlightInfo モデルのテスト."""

    def test_create_basic_flight(self):
        """基本的なフライト情報の作成."""
        flight = FlightInfo(
            flight_number="JAL515",
            airline="JAL",
            departure_airport="HND",
            arrival_airport="CTS",
            scheduled_departure=datetime(2025, 7, 1, 8, 0),
            scheduled_arrival=datetime(2025, 7, 1, 9, 35),
        )

        assert flight.flight_number == "JAL515"
        assert flight.airline == "JAL"
        assert flight.departure_airport == "HND"
        assert flight.arrival_airport == "CTS"
        assert flight.status == "scheduled"  # デフォルト値
        assert flight.terminal is None
        assert flight.gate is None

    def test_flight_duration_calculation(self):
        """フライト時間の計算."""
        flight = FlightInfo(
            flight_number="ANA001",
            airline="ANA",
            departure_airport="HND",
            arrival_airport="CTS",
            scheduled_departure=datetime(2025, 7, 1, 8, 0),
            scheduled_arrival=datetime(2025, 7, 1, 9, 35),
        )

        assert flight.flight_duration == timedelta(hours=1, minutes=35)
        assert flight.flight_duration.total_seconds() == 5700  # 95分

    def test_early_morning_flight_detection(self):
        """早朝便の判定."""
        # 早朝便（8時前）
        early_flight = FlightInfo(
            flight_number="JAL500",
            airline="JAL",
            departure_airport="HND",
            arrival_airport="CTS",
            scheduled_departure=datetime(2025, 7, 1, 6, 30),
            scheduled_arrival=datetime(2025, 7, 1, 8, 5),
        )
        assert early_flight.is_early_morning is True

        # 通常便（8時以降）
        normal_flight = FlightInfo(
            flight_number="JAL515",
            airline="JAL",
            departure_airport="HND",
            arrival_airport="CTS",
            scheduled_departure=datetime(2025, 7, 1, 9, 0),
            scheduled_arrival=datetime(2025, 7, 1, 10, 35),
        )
        assert normal_flight.is_early_morning is False

    def test_flight_with_full_details(self):
        """全詳細を含むフライト情報."""
        flight = FlightInfo(
            flight_number="NH001",
            airline="ANA",
            departure_airport="HND",
            arrival_airport="ITM",
            scheduled_departure=datetime(2025, 7, 1, 10, 0),
            scheduled_arrival=datetime(2025, 7, 1, 11, 15),
            terminal="2",
            gate="65",
            seat="12A",
            confirmation_code="ABC123",
            status="delayed",
        )

        assert flight.terminal == "2"
        assert flight.gate == "65"
        assert flight.seat == "12A"
        assert flight.confirmation_code == "ABC123"
        assert flight.status == "delayed"


# AccommodationInfo Tests
class TestAccommodationInfo:
    """AccommodationInfo モデルのテスト."""

    def test_create_basic_accommodation(self):
        """基本的な宿泊情報の作成."""
        hotel = AccommodationInfo(
            name="札幌グランドホテル",
            type="hotel",
            check_in=datetime(2025, 7, 1, 15, 0),
            check_out=datetime(2025, 7, 3, 11, 0),
            address="札幌市中央区北1条西4丁目",
        )

        assert hotel.name == "札幌グランドホテル"
        assert hotel.type == "hotel"
        assert hotel.address == "札幌市中央区北1条西4丁目"
        assert hotel.phone is None
        assert hotel.confirmation_code is None

    def test_nights_calculation(self):
        """宿泊日数の計算."""
        # 2泊
        hotel_2nights = AccommodationInfo(
            name="テストホテル",
            type="hotel",
            check_in=datetime(2025, 7, 1, 15, 0),
            check_out=datetime(2025, 7, 3, 11, 0),
            address="東京都千代田区",
        )
        assert hotel_2nights.nights == 2

        # 1泊
        hotel_1night = AccommodationInfo(
            name="テスト旅館",
            type="ryokan",
            check_in=datetime(2025, 7, 1, 15, 0),
            check_out=datetime(2025, 7, 2, 10, 0),
            address="箱根町",
        )
        assert hotel_1night.nights == 1

    def test_accommodation_types(self):
        """異なる宿泊タイプ."""
        # ホテル
        hotel = AccommodationInfo(
            name="ビジネスホテル",
            type="hotel",
            check_in=datetime(2025, 7, 1, 15, 0),
            check_out=datetime(2025, 7, 2, 11, 0),
            address="大阪市",
        )
        assert hotel.type == "hotel"

        # 旅館
        ryokan = AccommodationInfo(
            name="温泉旅館",
            type="ryokan",
            check_in=datetime(2025, 7, 1, 15, 0),
            check_out=datetime(2025, 7, 2, 10, 0),
            address="草津温泉",
        )
        assert ryokan.type == "ryokan"

        # Airbnb
        airbnb = AccommodationInfo(
            name="京都の町家",
            type="airbnb",
            check_in=datetime(2025, 7, 1, 16, 0),
            check_out=datetime(2025, 7, 3, 10, 0),
            address="京都市東山区",
        )
        assert airbnb.type == "airbnb"


# TransportSegment Tests
class TestTransportSegment:
    """TransportSegment モデルのテスト."""

    def test_create_train_segment(self):
        """電車移動区間の作成."""
        train = TransportSegment(
            type="train",
            provider="JR東日本",
            from_location="東京駅",
            to_location="品川駅",
            departure_time=datetime(2025, 7, 1, 9, 0),
            arrival_time=datetime(2025, 7, 1, 9, 15),
            reservation_required=False,
        )

        assert train.type == "train"
        assert train.provider == "JR東日本"
        assert train.from_location == "東京駅"
        assert train.to_location == "品川駅"
        assert train.reservation_required is False

    def test_create_bus_segment_with_reservation(self):
        """予約必須のバス移動区間."""
        bus = TransportSegment(
            type="bus",
            provider="北海道中央バス",
            from_location="新千歳空港",
            to_location="札幌駅",
            departure_time=datetime(2025, 7, 1, 10, 30),
            arrival_time=datetime(2025, 7, 1, 11, 30),
            reservation_required=True,
            confirmation_code="BUS123",
        )

        assert bus.reservation_required is True
        assert bus.confirmation_code == "BUS123"


# Meeting Tests
class TestMeeting:
    """Meeting モデルのテスト."""

    def test_create_basic_meeting(self):
        """基本的な会議情報の作成."""
        meeting = Meeting(
            title="プロジェクトキックオフ",
            location="札幌オフィス 会議室A",
            start_time=datetime(2025, 7, 1, 14, 0),
            end_time=datetime(2025, 7, 1, 16, 0),
        )

        assert meeting.title == "プロジェクトキックオフ"
        assert meeting.location == "札幌オフィス 会議室A"
        assert meeting.attendees == []  # デフォルト値
        assert meeting.notes is None

    def test_meeting_with_attendees_and_notes(self):
        """参加者と備考を含む会議."""
        meeting = Meeting(
            title="営業会議",
            location="東京本社",
            start_time=datetime(2025, 7, 2, 10, 0),
            end_time=datetime(2025, 7, 2, 12, 0),
            attendees=["田中", "佐藤", "鈴木"],
            notes="資料は前日までに配布",
        )

        assert len(meeting.attendees) == 3
        assert "田中" in meeting.attendees
        assert meeting.notes == "資料は前日までに配布"


# TripItinerary Tests
class TestTripItinerary:
    """TripItinerary モデルのテスト."""

    @pytest.fixture
    def sample_itinerary(self) -> TripItinerary:
        """テスト用の旅行行程を作成."""
        flights = [
            FlightInfo(
                flight_number="JAL515",
                airline="JAL",
                departure_airport="HND",
                arrival_airport="CTS",
                scheduled_departure=datetime(2025, 7, 1, 8, 0),
                scheduled_arrival=datetime(2025, 7, 1, 9, 35),
            ),
            FlightInfo(
                flight_number="JAL522",
                airline="JAL",
                departure_airport="CTS",
                arrival_airport="HND",
                scheduled_departure=datetime(2025, 7, 3, 19, 30),
                scheduled_arrival=datetime(2025, 7, 3, 21, 10),
            ),
        ]

        accommodations = [
            AccommodationInfo(
                name="札幌グランドホテル",
                type="hotel",
                check_in=datetime(2025, 7, 1, 15, 0),
                check_out=datetime(2025, 7, 3, 11, 0),
                address="札幌市中央区",
            )
        ]

        transport_segments = [
            TransportSegment(
                type="train",
                provider="JR北海道",
                from_location="新千歳空港",
                to_location="札幌駅",
                departure_time=datetime(2025, 7, 1, 10, 15),
                arrival_time=datetime(2025, 7, 1, 10, 52),
            )
        ]

        meetings = [
            Meeting(
                title="クライアント会議",
                location="札幌オフィス",
                start_time=datetime(2025, 7, 2, 10, 0),
                end_time=datetime(2025, 7, 2, 12, 0),
            )
        ]

        return TripItinerary(
            trip_id="20250701-sapporo-business",
            flights=flights,
            accommodations=accommodations,
            transport_segments=transport_segments,
            meetings=meetings,
        )

    def test_create_itinerary(self, sample_itinerary: TripItinerary):
        """旅行行程の作成."""
        assert sample_itinerary.trip_id == "20250701-sapporo-business"
        assert len(sample_itinerary.flights) == 2
        assert len(sample_itinerary.accommodations) == 1
        assert len(sample_itinerary.transport_segments) == 1
        assert len(sample_itinerary.meetings) == 1

    def test_timeline_events(self, sample_itinerary: TripItinerary):
        """タイムラインイベントの生成と順序."""
        events = sample_itinerary.timeline_events

        # イベント数の確認（往復フライト×2 + ホテル×2 + 電車×1 + 会議×1 = 8）
        assert len(events) == 8

        # 時系列順になっているか確認
        for i in range(1, len(events)):
            assert events[i - 1][0] <= events[i][0]

        # 最初のイベントは出発便
        assert events[0][1] == "flight_departure"
        assert "JAL515" in events[0][2]

        # 最後のイベントは帰着便
        assert events[-1][1] == "flight_arrival"
        assert "HND" in events[-1][2]

    def test_empty_itinerary(self):
        """空の旅行行程."""
        itinerary = TripItinerary(trip_id="test-empty")

        assert itinerary.trip_id == "test-empty"
        assert len(itinerary.flights) == 0
        assert len(itinerary.accommodations) == 0
        assert len(itinerary.transport_segments) == 0
        assert len(itinerary.meetings) == 0
        assert len(itinerary.timeline_events) == 0

    def test_timeline_event_types(self, sample_itinerary: TripItinerary):
        """タイムラインイベントの種類を確認."""
        events = sample_itinerary.timeline_events
        event_types = {event[1] for event in events}

        expected_types = {
            "flight_departure",
            "flight_arrival",
            "hotel_checkin",
            "hotel_checkout",
            "transport",
            "meeting",
        }

        assert event_types == expected_types
