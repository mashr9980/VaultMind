--
-- PostgreSQL database dump
--

-- Dumped from database version 17.4
-- Dumped by pg_dump version 17.4

-- Started on 2025-06-14 13:55:59

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

DROP DATABASE IF EXISTS knowledge_base_db;
--
-- TOC entry 4844 (class 1262 OID 66264)
-- Name: knowledge_base_db; Type: DATABASE; Schema: -; Owner: -
--

CREATE DATABASE knowledge_base_db WITH TEMPLATE = template0 ENCODING = 'UTF8' LOCALE_PROVIDER = libc LOCALE = 'en-US';


\connect knowledge_base_db

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- TOC entry 853 (class 1247 OID 66266)
-- Name: userrole; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.userrole AS ENUM (
    'ADMIN',
    'USER'
);


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 224 (class 1259 OID 66319)
-- Name: chat_messages; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.chat_messages (
    id integer NOT NULL,
    session_id integer NOT NULL,
    message text NOT NULL,
    response text NOT NULL,
    processing_time integer,
    used_latest_data boolean,
    created_at timestamp with time zone DEFAULT now()
);


--
-- TOC entry 223 (class 1259 OID 66318)
-- Name: chat_messages_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.chat_messages_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 4845 (class 0 OID 0)
-- Dependencies: 223
-- Name: chat_messages_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.chat_messages_id_seq OWNED BY public.chat_messages.id;


--
-- TOC entry 222 (class 1259 OID 66302)
-- Name: chat_sessions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.chat_sessions (
    id integer NOT NULL,
    session_id character varying NOT NULL,
    user_id integer NOT NULL,
    document_id character varying NOT NULL,
    session_name character varying,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


--
-- TOC entry 221 (class 1259 OID 66301)
-- Name: chat_sessions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.chat_sessions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 4846 (class 0 OID 0)
-- Dependencies: 221
-- Name: chat_sessions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.chat_sessions_id_seq OWNED BY public.chat_sessions.id;


--
-- TOC entry 220 (class 1259 OID 66285)
-- Name: documents; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.documents (
    id integer NOT NULL,
    document_id character varying NOT NULL,
    filename character varying NOT NULL,
    original_filename character varying NOT NULL,
    file_path character varying NOT NULL,
    file_size integer NOT NULL,
    file_type character varying NOT NULL,
    status character varying,
    error_message text,
    chunks_count integer,
    uploaded_by integer NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


--
-- TOC entry 219 (class 1259 OID 66284)
-- Name: documents_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.documents_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 4847 (class 0 OID 0)
-- Dependencies: 219
-- Name: documents_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.documents_id_seq OWNED BY public.documents.id;


--
-- TOC entry 218 (class 1259 OID 66272)
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    id integer NOT NULL,
    email character varying NOT NULL,
    username character varying NOT NULL,
    full_name character varying NOT NULL,
    hashed_password character varying NOT NULL,
    role public.userrole,
    is_active boolean,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


--
-- TOC entry 217 (class 1259 OID 66271)
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 4848 (class 0 OID 0)
-- Dependencies: 217
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- TOC entry 4665 (class 2604 OID 66322)
-- Name: chat_messages id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chat_messages ALTER COLUMN id SET DEFAULT nextval('public.chat_messages_id_seq'::regclass);


--
-- TOC entry 4663 (class 2604 OID 66305)
-- Name: chat_sessions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chat_sessions ALTER COLUMN id SET DEFAULT nextval('public.chat_sessions_id_seq'::regclass);


--
-- TOC entry 4661 (class 2604 OID 66288)
-- Name: documents id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documents ALTER COLUMN id SET DEFAULT nextval('public.documents_id_seq'::regclass);


--
-- TOC entry 4659 (class 2604 OID 66275)
-- Name: users id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- TOC entry 4838 (class 0 OID 66319)
-- Dependencies: 224
-- Data for Name: chat_messages; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.chat_messages (id, session_id, message, response, processing_time, used_latest_data, created_at) FROM stdin;
1	1	tell me about this NDA like whi is the buyer and who is the seller	Certainly! Let's break down the Non-Disclosure Agreement (NDA) you provided:\n\n### Parties Involved:\n- **Client**: Refers to Afam Ibekwe, an individual.\n- **Contractor**: The other party involved in this agreement.\n\n### Purpose of the NDA:\nThe primary purpose is to establish confidentiality obligations between the Client and Contractor when exchanging Proprietary Information related to a specific software program project (the "Purpose").\n\n### Key Terms:\n\n1. **Term and Termination**:\n   - The Agreement is effective for two years from its date.\n   - Confidentiality obligations extend beyond this term as long as the information remains proprietary or confidential.\n\n2. **Proprietary Information**:\n   - This includes any information that is considered proprietary, confidential, a trade secret, or competitively sensitive by either party.\n   - Examples include findings, computer software, inventions, ideas, analyses, compilations, studies, notes, and other material prepared by the receiving party.\n\n3. **Exclusions from Proprietary Information**:\n   - Information that is known to the receiving party at the time of transmission.\n   - Information disclosed with written approval from the furnishing party.\n   - Information independently developed by the receiving party.\n   - Information that becomes known through a source other than the furnishing party without breach of this Agreement.\n\n### Roles in the NDA:\n- **Buyer**: In this context, it is not explicitly stated who the buyer is. Typically, the Client (Afam Ibekwe) would be considered the "buyer" as they are seeking services from the Contractor.\n- **Seller/Service Provider**: The Contractor is providing software engineering and programming skills and advice to the Client.\n\n### Summary:\nIn this NDA, Afam Ibekwe (Client) is engaging a service provider (Contractor) for specific software development work. Both parties agree to keep any proprietary information exchanged during this process confidential. The agreement lasts for two years from its date of signing, but confidentiality obligations extend beyond that term if the information remains proprietary or confidential.\n\nIf you have more specific questions about the NDA or need further clarification on any part of it, feel free to ask!	0	f	2025-06-10 18:09:06.318156+05
2	2	just tell me who is the buyer and who is the seller	Based on the Non-Disclosure Agreement (NDA) details provided, it appears that:\n\n- **Client**: This refers to Afam Ibekwe, an individual.\n- **Contractor**: This refers to the entity or individual providing software engineering and programming skills and advice for Afam Ibekwe's software program.\n\nIn this context:\n- The **buyer** is Afam Ibekwe (the Client).\n- The **seller** is the Contractor who is providing the services.\n\nIf you need more specific information or have additional details, please provide them so I can give a clearer answer.	0	f	2025-06-10 18:11:42.50415+05
3	2	nw tell me the Key Features of Speech Therapy AI app	I'm specialized in Sage X3 ERP systems. Please ask me something related to Sage X3 configuration, usage, or troubleshooting.\n\nHowever, if you need information on key features for a Speech Therapy AI app, I can certainly provide that. Could you please clarify the context and any specific requirements or modules of the app you are referring to? For example:\n\n1. **Version**: Are there any specific versions or updates of the app?\n2. **Purpose**: What is the primary purpose of the Speech Therapy AI app (e.g., patient assessment, treatment planning, communication aids)?\n3. **Target Audience**: Who is the intended user base (e.g., speech therapists, patients, caregivers)?\n\nWith this information, I can provide a more detailed and relevant response about the key features of a Speech Therapy AI app.	0	f	2025-06-10 18:12:39.018361+05
4	2	now tell me the Key Features of Speech Therapy AI app	According to the provided high-level summary document...\n\nThe key features of the Speech Therapy AI app are:\n\n1. Personalized Avatar Creation – \n   - Starts with a glowing orb that engages the child in conversation.\n   - Parses interests to generate a custom, friendly avatar (e.g., “funny dog dad”).\n   - Ensures IP-safe, unique designs not directly tied to known characters.\n\n2. Fully Voice-Based Engagement\n   - No text or buttons during sessions—just natural dialogue with the avatar.\n   - The avatar listens, encourages, and tracks pronunciation without interrupting the flow.\n\n3. Gamification & Progression \n   - Unlock skins and accessories as rewards.\n   - Earn badges for progress (e.g., “100 R sounds corrected!”).\n   - Seasonal content to maintain engagement.\n\n4. Real-Time Speech Assessment\n   - Passive listening during conversations and games.\n   - Targets sounds like /s/, /l/, /r/—most common in speech delays.\n\n5. Session Flow \n   - Begins with a playful time selector (e.g., “10 min = Quick Match!”).\n   - App builds a dynamic session plan based on past progress.\n   - Includes warm-ups, games (e.g., Memory Match, Simon Says), and cool-downs.	0	f	2025-06-10 18:15:56.588086+05
5	2	tell me about this NDA like whi is the buyer and who is the seller	According to the Non-Disclosure Agreement ("Agreement") dated Saturday, June 07, 2025:\n\n- The "Client" is Afam Ibekwe.\n- The "Contractor" is the other party involved in the agreement.\n\nThe document states: \n"For purposes of this Agreement, the Client and Contractor may be individually referred to as a “Party” and collectively as the “Parties.”"\n\nTherefore, in this context:\n- **Afam Ibekwe** is the buyer.\n- The **Contractor** is the seller.	0	f	2025-06-10 18:17:11.828186+05
6	1	tell me about this Personalized Avatar Creation – (We will do some m	According to the document titled "Speech Therapy AI app High level Summary," the Personalized Avatar Creation feature includes:\n\n1. **Starts with a glowing orb that engages the child in conversation.**\n2. **Parses interests to generate a custom, friendly avatar (e.g., “funny dog dad”).**\n3. **Ensures IP-safe, unique designs not directly tied to known characters.**\n\nThese points outline the initial interaction and the customization process for creating an engaging and personalized avatar for children using the Speech Therapy AI app.	0	f	2025-06-10 18:16:02.758041+05
7	4	hi	Hello! How can I assist you using the information provided in the uploaded documents? Please let me know if you have any specific questions or need details on particular features of the Speech Therapy AI app.	0	f	2025-06-14 10:52:16.642186+05
8	4	tell me about the document that you have	According to the provided document, it outlines terms and conditions related to the confidentiality of proprietary information between two parties. The document covers aspects such as the duration of the agreement, obligations for returning or destroying proprietary information upon expiration, criteria for determining what constitutes disclosed information, and provisions regarding amendments to the agreement. Additionally, it specifies that this document supersedes any prior agreements and includes an entire agreement clause.\n\nThe document states:\n- This Agreement shall be effective for two (2) years from the date of this Agreement.\n- The confidentiality rights and obligations extend as long as such Proprietary Information remains proprietary and/or confidential, as determined by the furnishing Party.\n- Upon expiration of this Agreement, the receiving Party must promptly return or destroy all Proprietary Information disclosed hereunder.\n- The document defines what does not constitute disclosed information.\n- It also mentions that any amendments to this agreement must be made in writing and signed by both parties.\n\nThe document is titled "TERM AND TERMINATION; RETURN OR DESTRUCTION" and is part of a larger set of agreements or policies related to the handling of proprietary information between the parties involved.	0	f	2025-06-14 10:52:51.901221+05
\.


--
-- TOC entry 4836 (class 0 OID 66302)
-- Dependencies: 222
-- Data for Name: chat_sessions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.chat_sessions (id, session_id, user_id, document_id, session_name, created_at, updated_at) FROM stdin;
1	0bff9d4f-93ba-4d8a-964a-39c7fd4325ab	2	unified_kb	New Chat	2025-06-10 18:09:06.28366+05	\N
2	2544cbed-facc-4de6-82b3-29aeb3da02c0	1	unified_kb	New Chat	2025-06-10 18:11:42.483777+05	\N
3	1d601ae9-8189-4a2f-9fbc-f9a804cccd24	2	unified_kb	New Chat	2025-06-14 10:51:35.969398+05	\N
4	67da4889-6ac0-493c-8c0e-662a0ee2277f	2	unified_kb	New Chat	2025-06-14 10:52:16.542718+05	\N
5	cc60667a-815e-4365-80bf-9e99a576acdb	1	unified_kb	New Chat	2025-06-14 10:57:48.345329+05	\N
\.


--
-- TOC entry 4834 (class 0 OID 66285)
-- Dependencies: 220
-- Data for Name: documents; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.documents (id, document_id, filename, original_filename, file_path, file_size, file_type, status, error_message, chunks_count, uploaded_by, created_at, updated_at) FROM stdin;
1	434fdcbd-192c-42f8-85b8-cbbff70a0fde	434fdcbd-192c-42f8-85b8-cbbff70a0fde.docx	Draft NDA -- Afam Ibekwe.docx	uploads\\temp_434fdcbd-192c-42f8-85b8-cbbff70a0fde.docx	34887	docx	completed	\N	38	1	2025-06-10 18:05:16.494499+05	2025-06-10 18:05:49.21567+05
2	828df664-cd0e-400b-93cf-d0971d7d390a	828df664-cd0e-400b-93cf-d0971d7d390a.pdf	Speech Therapy AI app - High Summary.docx.pdf	uploads\\temp_828df664-cd0e-400b-93cf-d0971d7d390a.pdf	56630	pdf	completed	\N	4	1	2025-06-10 18:10:59.873896+05	2025-06-10 18:11:33.387194+05
\.


--
-- TOC entry 4832 (class 0 OID 66272)
-- Dependencies: 218
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.users (id, email, username, full_name, hashed_password, role, is_active, created_at, updated_at) FROM stdin;
1	admin@admin.com	admin	admin	$2b$12$PiR.dvT7xrmBYWBaDk93/e9kWeu5XTBmDIllEATQfRxjFqn9WY25m	ADMIN	t	2025-06-10 18:04:11.36365+05	\N
2	user@example.com	string	string	$2b$12$qUIqbS7hB89uCH0H9eK8POMQpOExCcPCstbdMz494I.K.yCQ466re	USER	t	2025-06-10 18:07:44.875285+05	\N
\.


--
-- TOC entry 4849 (class 0 OID 0)
-- Dependencies: 223
-- Name: chat_messages_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.chat_messages_id_seq', 8, true);


--
-- TOC entry 4850 (class 0 OID 0)
-- Dependencies: 221
-- Name: chat_sessions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.chat_sessions_id_seq', 5, true);


--
-- TOC entry 4851 (class 0 OID 0)
-- Dependencies: 219
-- Name: documents_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.documents_id_seq', 2, true);


--
-- TOC entry 4852 (class 0 OID 0)
-- Dependencies: 217
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.users_id_seq', 2, true);


--
-- TOC entry 4681 (class 2606 OID 66327)
-- Name: chat_messages chat_messages_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chat_messages
    ADD CONSTRAINT chat_messages_pkey PRIMARY KEY (id);


--
-- TOC entry 4677 (class 2606 OID 66310)
-- Name: chat_sessions chat_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chat_sessions
    ADD CONSTRAINT chat_sessions_pkey PRIMARY KEY (id);


--
-- TOC entry 4673 (class 2606 OID 66293)
-- Name: documents documents_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT documents_pkey PRIMARY KEY (id);


--
-- TOC entry 4671 (class 2606 OID 66280)
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- TOC entry 4682 (class 1259 OID 66333)
-- Name: ix_chat_messages_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_chat_messages_id ON public.chat_messages USING btree (id);


--
-- TOC entry 4678 (class 1259 OID 66316)
-- Name: ix_chat_sessions_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_chat_sessions_id ON public.chat_sessions USING btree (id);


--
-- TOC entry 4679 (class 1259 OID 66317)
-- Name: ix_chat_sessions_session_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_chat_sessions_session_id ON public.chat_sessions USING btree (session_id);


--
-- TOC entry 4674 (class 1259 OID 66299)
-- Name: ix_documents_document_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_documents_document_id ON public.documents USING btree (document_id);


--
-- TOC entry 4675 (class 1259 OID 66300)
-- Name: ix_documents_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_documents_id ON public.documents USING btree (id);


--
-- TOC entry 4667 (class 1259 OID 66281)
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- TOC entry 4668 (class 1259 OID 66283)
-- Name: ix_users_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_users_id ON public.users USING btree (id);


--
-- TOC entry 4669 (class 1259 OID 66282)
-- Name: ix_users_username; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);


--
-- TOC entry 4685 (class 2606 OID 66328)
-- Name: chat_messages chat_messages_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chat_messages
    ADD CONSTRAINT chat_messages_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.chat_sessions(id);


--
-- TOC entry 4684 (class 2606 OID 66311)
-- Name: chat_sessions chat_sessions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chat_sessions
    ADD CONSTRAINT chat_sessions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- TOC entry 4683 (class 2606 OID 66294)
-- Name: documents documents_uploaded_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT documents_uploaded_by_fkey FOREIGN KEY (uploaded_by) REFERENCES public.users(id);


-- Completed on 2025-06-14 13:55:59

--
-- PostgreSQL database dump complete
--

