import type {Ocean, Weather} from "../types";
const value = (item: number | null | undefined, suffix: string) => item == null ? "—" : `${Math.round(item * 10) / 10}${suffix}`;
export function Conditions({ocean, weather}: {ocean: Ocean; weather: Weather}) {
  return <div className="conditions-grid">
    <section className="panel"><div className="panel-title"><div><span className="eyebrow">NOAA / NDBC</span><h2>Ocean conditions</h2></div>{ocean.is_mock && <span className="mock-badge">Demo data</span>}</div>
      <dl><div><dt>Wave height</dt><dd>{value(ocean.wave_height_ft," ft")}</dd></div><div><dt>Dominant period</dt><dd>{value(ocean.dominant_period_sec," sec")}</dd></div><div><dt>Average period</dt><dd>{value(ocean.average_period_sec," sec")}</dd></div><div><dt>Water temp</dt><dd>{value(ocean.water_temp_f,"°F")}</dd></div></dl>
      <small>Station {ocean.station_id}{ocean.status_message && ` · ${ocean.status_message}`}</small>
    </section>
    <section className="panel"><div className="panel-title"><div><span className="eyebrow">OpenWeather</span><h2>Local weather</h2></div>{weather.is_mock && <span className="mock-badge">Demo data</span>}</div>
      <dl><div><dt>Temperature</dt><dd>{value(weather.temperature_f,"°F")}</dd></div><div><dt>Wind</dt><dd>{value(weather.wind_speed_mph," mph")}</dd></div><div><dt>Gusts</dt><dd>{value(weather.wind_gust_mph," mph")}</dd></div><div><dt>Visibility</dt><dd>{value(weather.visibility_m ? weather.visibility_m / 1000 : null," km")}</dd></div></dl>
      <small className="capitalize">{weather.condition}{weather.status_message && ` · ${weather.status_message}`}</small>
    </section>
  </div>;
}

