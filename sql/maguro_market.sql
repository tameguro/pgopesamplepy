create table employees (
	employee_id char(6) not null,
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
