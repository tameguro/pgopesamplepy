create table employees (
	employee_id char(6) not null,
	name text not null,
	nickname text not null,
	primary key (employee_id)
);

create table shifts (
	day date not null,
	employee_id char(6) not null,
	start_time time not null,
	end_time time not null,
	primary key (day, employee_id)
);
ALTER TABLE shifts ADD FOREIGN KEY (employee_id) REFERENCES employees (employee_id);

create view v_shifts (day, nickname, start_time, end_time) AS
SELECT
  s.day,
  e.nickname,
  s.start_time,
  s.end_time
FROM
  shifts s inner join employees e
    on s.employee_id = e.employee_id
;
