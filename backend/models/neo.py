from datetime import datetime
from typing import Optional
from sqlalchemy import (
    String, Float, Boolean, DateTime, Integer, Text, ForeignKey, JSON
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database import Base


class NEO(Base):
    """Near-Earth Object master record."""
    __tablename__ = "neos"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    designation: Mapped[Optional[str]] = mapped_column(String(64))
    is_potentially_hazardous: Mapped[bool] = mapped_column(Boolean, default=False)
    absolute_magnitude: Mapped[Optional[float]] = mapped_column(Float)
    estimated_diameter_min_km: Mapped[Optional[float]] = mapped_column(Float)
    estimated_diameter_max_km: Mapped[Optional[float]] = mapped_column(Float)
    nasa_jpl_url: Mapped[Optional[str]] = mapped_column(String(512))

    # Orbital elements (Keplerian)
    semi_major_axis: Mapped[Optional[float]] = mapped_column(Float)       # AU
    eccentricity: Mapped[Optional[float]] = mapped_column(Float)
    inclination: Mapped[Optional[float]] = mapped_column(Float)           # deg
    raan: Mapped[Optional[float]] = mapped_column(Float)                   # deg Ω
    arg_perihelion: Mapped[Optional[float]] = mapped_column(Float)        # deg ω
    mean_anomaly: Mapped[Optional[float]] = mapped_column(Float)          # deg M

    # Risk scoring
    risk_score: Mapped[Optional[float]] = mapped_column(Float)
    risk_tier: Mapped[Optional[str]] = mapped_column(String(16))          # LOW/MED/HIGH/CRITICAL

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    approaches: Mapped[list["CloseApproach"]] = relationship(
        "CloseApproach", back_populates="neo", cascade="all, delete-orphan"
    )


class CloseApproach(Base):
    """Historical and future close approach records."""
    __tablename__ = "close_approaches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    neo_id: Mapped[str] = mapped_column(ForeignKey("neos.id", ondelete="CASCADE"))
    approach_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    miss_distance_km: Mapped[float] = mapped_column(Float, nullable=False)
    miss_distance_ld: Mapped[float] = mapped_column(Float, nullable=False)
    relative_velocity_kmps: Mapped[float] = mapped_column(Float, nullable=False)

    # Monte Carlo uncertainty (km)
    uncertainty_plus_km: Mapped[Optional[float]] = mapped_column(Float)
    uncertainty_minus_km: Mapped[Optional[float]] = mapped_column(Float)

    orbiting_body: Mapped[str] = mapped_column(String(32), default="Earth")

    neo: Mapped["NEO"] = relationship("NEO", back_populates="approaches")


class AlertLog(Base):
    """Persisted WebSocket alert events."""
    __tablename__ = "alert_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    neo_id: Mapped[str] = mapped_column(String(64))
    neo_name: Mapped[str] = mapped_column(String(256))
    miss_distance_ld: Mapped[float] = mapped_column(Float)
    approach_date: Mapped[str] = mapped_column(String(32))
    triggered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    payload: Mapped[Optional[dict]] = mapped_column(JSON)
