--
-- PostgreSQL database dump
--

SET statement_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

--
-- Name: plpgsql; Type: EXTENSION; Schema: -; Owner: 
--

CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;


--
-- Name: EXTENSION plpgsql; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';


SET search_path = public, pg_catalog;

--
-- Name: notify_trigger(); Type: FUNCTION; Schema: public; Owner: kolaborator
--

CREATE FUNCTION notify_trigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
BEGIN
	  PERFORM pg_notify('kolaborator', TG_TABLE_NAME || ',id,' || NEW.id );
	  RETURN new;
END;
$$;


ALTER FUNCTION public.notify_trigger() OWNER TO kolaborator;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: infringements; Type: TABLE; Schema: public; Owner: kolaborator; Tablespace: 
--

CREATE TABLE infringements (
	    id integer NOT NULL,
	    case_id text,
	    complainant_entity text,
	    complainant_email text,
	    provider_entity text,
	    provider_email text,
	    xml xml,
	    status text,
	    subject text,
	    message_id text,
	    filename text,
	    content_timestamp timestamp with time zone,
	    port integer,
	    ip_address inet,
	    source_timestamp timestamp with time zone
);


ALTER TABLE public.infringements OWNER TO kolaborator;

--
-- Name: infringements_id_seq; Type: SEQUENCE; Schema: public; Owner: kolaborator
--

CREATE SEQUENCE infringements_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.infringements_id_seq OWNER TO kolaborator;

--
-- Name: infringements_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: kolaborator
--

ALTER SEQUENCE infringements_id_seq OWNED BY infringements.id;


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: kolaborator
--

ALTER TABLE ONLY infringements ALTER COLUMN id SET DEFAULT nextval('infringements_id_seq'::regclass);


--
-- Name: infringements_pkey; Type: CONSTRAINT; Schema: public; Owner: kolaborator; Tablespace: 
--

ALTER TABLE ONLY infringements
    ADD CONSTRAINT infringements_pkey PRIMARY KEY (id);


--
-- Name: watched_table_trigger; Type: TRIGGER; Schema: public; Owner: kolaborator
--

CREATE TRIGGER watched_table_trigger AFTER INSERT ON infringements FOR EACH ROW EXECUTE PROCEDURE notify_trigger();


--
-- Name: public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM postgres;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- PostgreSQL database dump complete
--

