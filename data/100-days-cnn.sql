select l.url from forums_link as l
left join forums_forum as f on f.id = l.forum_id
left join forums_thread as t on t.id = l.thread_id
where f.url = 'cnn' and t.date >= current_date-100 and t.date < current_date and l.url='http://myearmark.com/2013/40369'